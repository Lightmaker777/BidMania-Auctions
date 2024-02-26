from django import forms
from .models import Auction

class CreateLiveAuctionForm(forms.ModelForm):
    twitch_username = forms.CharField(max_length=255, label='Twitch Username')
    image_url = forms.URLField(required=False, label='Image URL')
    image_upload = forms.ImageField(required=False, label='Upload Image')

    class Meta:
        model = Auction
        fields = ['title', 'description', 'start_bid', 'category', 'twitch_username', 'image_url', 'image_upload']
