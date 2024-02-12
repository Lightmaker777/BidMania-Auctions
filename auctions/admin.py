from django.contrib import admin
from .models import User, Category,  Auction, Comment, Bid

# Register your models here.
admin.site.register(User)
admin.site.register(Category)
admin.site.register(Bid)
admin.site.register(Auction)
admin.site.register(Comment)
