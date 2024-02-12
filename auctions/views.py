from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from .models import User, Auction, Category, Bid, Comment


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
        category = Category.objects.get(category=request.POST['category'])
        new_listing = Auction(
            title=title,
            description=description,
            start_bid=start_bid,
            image=image,
            category=category,
            lister=request.user)
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
