from django import forms
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass
    watchlist = models.ManyToManyField("Auction", blank=True, related_name="watcher")
    bids = models.ManyToManyField("Auction", blank=True, related_name="bidder")


class Category(models.Model):
    category = models.CharField(max_length=255)
    
    class Meta:
        ordering = ["category"]
    
    def __str__(self):
        return self.category


class Stream(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    streamer = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    twitch_username = models.CharField(max_length=255)
    twitch_stream_id = models.CharField(max_length=255, null=True, blank=True)


class Auction(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_bid = models.FloatField()
    image = models.URLField(blank=True)
    image_upload = forms.ImageField(required=False, label='Upload Image')
    category = models.ForeignKey(Category, on_delete=models.SET_DEFAULT, default="")
    lister = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name="lister")
    active = models.BooleanField(default=True)
    stream = models.OneToOneField(Stream, on_delete=models.CASCADE, null=True, blank=True)
    is_live_auction = models.BooleanField(default=False)
    class Meta:
        ordering = ["title"]
    
    def __str__(self):
        return f"{self.title} by {self.lister}"

    def num_of_bids(self):
        return len(self.bids.all())

    def current_bid(self):
        if len(self.bids.all()) == 0:
            return self.start_bid
        else:
            return self.bids.all().order_by("-new_bid").first().new_bid
        
    def highest_bidder(self):
        return self.bids.all().order_by("-new_bid").first().user

    def num_of_watcher(self):
        return len(self.watcher.all())


class Bid(models.Model):
    listing = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name="bids")
    new_bid = models.FloatField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ["listing"]

    def __str__(self):
        return f"{self.listing}: {self.user} bids {self.new_bid}"


class Comment(models.Model):
    listing = models.ForeignKey(Auction, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default="deleted_user")
    date = models.DateTimeField(auto_now_add=True)
    comment = models.TextField()

    class Meta:
        ordering = ["listing"]

    def __str__(self):
        return f"{self.listing}: {self.user} commented {self.comment}"