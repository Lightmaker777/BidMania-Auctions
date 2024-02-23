from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import User, Auction, Category, Bid, Comment, Stream
from .forms import CreateLiveAuctionForm 
from django.conf import settings
from twitch import TwitchClient
from django.db.models import Q
import requests
from django.contrib import messages



# Twitch authentication and callback
from twitch import TwitchClient

def twitch_authenticate(request):
    twitch_redirect_uri = request.build_absolute_uri(reverse('twitch_callback'))
    twitch_auth_url = f'https://id.twitch.tv/oauth2/authorize?client_id={settings.TWITCH_CLIENT_ID}&redirect_uri={twitch_redirect_uri}&response_type=code&scope=user_read'
    return redirect(twitch_auth_url)

def twitch_callback(request):
    client = TwitchClient(client_id=settings.TWITCH_CLIENT_ID, client_secret=settings.TWITCH_CLIENT_SECRET)
    code = request.GET.get('code', None)
    token, refresh_token = client.exchange_code(code, settings.TWITCH_REDIRECT_URI)
    return render(request, 'twitch_callback.html', {'twitch_access_token': token.access_token})


# Active listings
def index(request):
    return render(request, "auctions/index.html", {
        "auctions": Auction.objects.filter(active=True),
        "headline": "Active Listings"
    })


# Active and closed listings
def all(request):
    return render(request, "auctions/index.html", {
        "auctions": Auction.objects.all(),
        "headline": "All Listings"
    })

@login_required(login_url='login')
def live_auctions(request):
    live_auctions = Auction.objects.filter(stream__isnull=False, active=True)
    return render(request, "auctions/live_auctions.html", {
        "live_auctions": live_auctions,
        "headline": "Live Auctions"
    })


# View for listing all live auctions from all users
@login_required(login_url='login')
def all_live_auctions(request):
    live_auctions = Auction.objects.filter(
        Q(stream__isnull=False) & Q(active=True)
    )
    return render(request, "auctions/all_live_auctions.html", {
        "live_auctions": live_auctions,
        "headline": "All Live Auctions"
    })

@login_required(login_url='login')
def live_stream(request, auction_id):
    auction = get_object_or_404(Auction, pk=auction_id, active=True)
    # You can pass the auction details to the template for rendering Twitch stream
    return render(request, 'auctions/live_stream.html', {'auction': auction})

def live_stream_auction(request, auction_id):
    auction = get_object_or_404(Auction, pk=auction_id, active=True)
    # Your logic for rendering the live stream page goes here
    return render(request, 'auctions/live_stream_auction.html', {'auction': auction})

@login_required(login_url='login')
def create_live_auctions(request):
    if request.method == "POST":
        form = CreateLiveAuctionForm(request.POST, request.FILES)
        if form.is_valid():
            title = form.cleaned_data['title']
            description = form.cleaned_data['description']
            start_bid = form.cleaned_data['start_bid']
            category = Category.objects.get(category=form.cleaned_data['category'])
            
            # Create a new auction
            new_auction = Auction(
                title=title,
                description=description,
                start_bid=start_bid,
                category=category,
                lister=request.user,
                is_live_auction=True  # Set is_live_auction to True for live stream auctions
            )

            # Check if an image URL is provided
            if form.cleaned_data['image_url']:
                new_auction.image = form.cleaned_data['image_url']
            elif form.cleaned_data['image_upload']:
                new_auction.image = form.cleaned_data['image_upload']

            new_auction.save()

            # Create a new stream associated with the auction
            twitch_username = form.cleaned_data['twitch_username']
            stream = Stream(
                title=title,
                description=description,
                streamer=request.user,
                twitch_username=twitch_username,
                twitch_stream_id=get_twitch_stream_id(twitch_username)  # Implement this function
            )
            stream.save()

            # Link the stream to the auction
            new_auction.stream = stream
            new_auction.save()

            return redirect("live_auctions")  # Redirect to the auction listing or any other page
    else:
        form = CreateLiveAuctionForm()

    return render(request, "auctions/create_live_auctions.html", {
        "form": form,
        "categories": Category.objects.all(),
        "headline": "Create Live Auctions",
        "user_id": request.user.id  # Pass the user's ID to the template
    })

# Function to get Twitch stream ID
def get_twitch_stream_id(username):
    # Replace 'YOUR_TWITCH_CLIENT_ID' with your actual Twitch client ID
    twitch_client_id = 'TWITCH_CLIENT_ID'
    
    # Twitch API endpoint for getting user information
    api_url = f'https://api.twitch.tv/helix/users?login={username}'
    
    # Set up headers with Twitch client ID
    headers = {
        'Client-ID': twitch_client_id,
    }

    try:
        # Make a GET request to the Twitch API
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse the JSON response
        user_data = response.json()
        
        # Extract and return the user's ID
        user_id = user_data['data'][0]['id']
        return user_id
    except requests.exceptions.RequestException as e:
        # Handle request errors
        print(f"Error accessing Twitch API: {e}")
        return None


# Closed listings
def closed(request):
    return render(request, "auctions/index.html", {
        "auctions": Auction.objects.filter(active=False),
        "headline": "Closed Listings"
    })


# Categories on navbar
def categories(request):
    return render(request, "auctions/categories.html", {
        "categories": Category.objects.all(),
        "headline": f"Categories"
    })


# Active listing on each category in categories
def listing_category(request, category_name):
    category = Category.objects.get(category=category_name)
    return render(request, "auctions/index.html", {
        "auctions": Auction.objects.filter(category=category, active=True),
        "headline": f"Category: {category_name}"
    })


# Watchlist on navbar
@login_required(login_url='login')
def watchlists(request):
    watchlist = request.user.watchlist.all()
    return render(request, "auctions/index.html", {
        "auctions": watchlist,
        "headline": "Watchlist"
    })


# Adds / remove listing to / from watchlist
@login_required(login_url='login')
def watchlist(request, id):
    if request.method == "POST":
        auction = Auction.objects.get(pk=id)
        watchlist = request.user.watchlist.all()
        # User remove listing from watchlist
        if auction in watchlist:
            request.user.watchlist.remove(auction)
            message = "Removed from Watchlist!"
        # User adds listing to watchlist
        else:
            request.user.watchlist.add(auction)
            message = "Added to Watchlist!"
        return render(request, "auctions/listing.html", {
            "auction": auction,
            "message": message
        })


# Create new listing
@login_required(login_url='login')
def create(request):
    # User clicks "create listing" on navbar
    if request.method == "GET":
        return render(request, "auctions/create.html", {
            "categories": Category.objects.all(),
            "headline": "Create Listing"
        })
    # User submits listing
    else:
        title = request.POST['title']
        description = request.POST['description']
        start_bid = request.POST['start_bid']
        image = request.POST['image']
        image_upload = request.POST['image_upload']
        category = Category.objects.get(category=request.POST['category'])
        new_listing = Auction(
            title=title,
            description=description,
            start_bid=start_bid,
            image=image,
            image_upload=image_upload,
            category=category,
            lister=request.user)
        
   # Check if an image URL is provided
        if 'image' in request.POST and request.POST['image']:
            new_listing.image = request.POST['image']
        # Check if an image file is uploaded
        elif 'image_upload' in request.FILES:
            new_listing.image = request.FILES['image_upload']  

        new_listing.save()
        return redirect("index")



# Listing page
def listing(request, id):
    return render(request, "auctions/listing.html", {
        "auction": Auction.objects.get(pk=id),
        "comments": Comment.objects.filter(listing=id)
    })

def listed_by(request, username):
    lister = User.objects.get(username=username)
    return render(request, "auctions/index.html", {
        "auctions": Auction.objects.filter(lister=lister),
        "headline": f"Listings by {username}"
    })

@login_required(login_url='login')
def comment(request, id):
    if request.method == "POST":
        listing = Auction.objects.get(pk=id)
        comment = request.POST['comment']
        new_comment = Comment(listing=listing, user=request.user, comment=comment)
        new_comment.save()
        return redirect("listing", id=id)

@login_required(login_url='login')
def bid(request, id):
    if request.method == "POST":
        auction = Auction.objects.get(pk=id)
        amount = float(request.POST['bid'])
        if auction.current_bid() > amount and auction.lister != request.user and auction.active == True:
            return render(request, "auctions/listing.html", {
                "auction": auction,
                "message": "Amount should be higher than the current bid!"})
        elif auction.lister == request.user:
            return render(request, "auctions/listing.html", {
                "auction": auction,
                "message": "Can't bid on your own listing!"
            })
        elif auction.active == False:
            return render(request, "auctions/listing.html", {
                "auction": auction,
                "message": "Can't bid on closed listing!"
            })
        else:
            bid = Bid(listing=auction, new_bid=amount, user=request.user)
            bid.save()
            request.user.bids.add(auction)
            return redirect("listing", id=id)

@login_required(login_url='login')
def close(request, id):
    if request.method == "POST":
        auction = Auction.objects.get(pk=id)
        auction.active = False
        auction.save()
        return redirect("listing", id=id)

@login_required(login_url='login')
def activate(request, id):
    if request.method == "POST":
        auction = Auction.objects.get(pk=id)
        auction.active = True
        auction.save()
        return render(request, "auctions/listing.html", {
            "auction": auction,
            "message": "Listing active!"
        })



# User-related
def my_listings(request):
    return render(request, "auctions/index.html", {
        "auctions": Auction.objects.filter(lister=request.user),
        "headline": "My Listings"
    })

def my_bids(request):
    mybids = request.user.bids.all()
    return render(request, "auctions/index.html", {
        "auctions": mybids,
        "headline": "My Bids"
    })

def login_view(request):
    headline = "Login"
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password.",
                "headline": headline
            })
    else:
        return render(request, "auctions/login.html", {
            "headline": headline
        })

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def register(request):
    headline = "Register"
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match.",
                "headline": headline
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken.",
                "headline": headline
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html", {
            "headline": headline
        })

# PayPal
def success_page(request):
    return render(request, "auctions/success_page.html")

