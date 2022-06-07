import locale
from re import template

from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views import generic

from .models import AuctionSetting, Item, Bid
from urllib.parse import quote


class AuctionSettingMixin(generic.base.ContextMixin):
  def get_context_data(self, **kwargs):
    ctxt = super().get_context_data(**kwargs)
    ctxt["auction_setting"] = AuctionSetting.objects.filter(active=True).order_by("id").first()
    return ctxt


class NameInputView(AuctionSettingMixin, generic.TemplateView):
  template_name = 'name_input.html'

  def post(self, request, *args, **kwargs):
    return HttpResponseRedirect("/bidding/?name=" + quote(request.POST["name"]) + "&phone_number=" + quote(request.POST["phone_number"]))
        


class BiddingView(AuctionSettingMixin, generic.TemplateView):
  template_name = 'bidding.html'

  def get_context_data(self, **kwargs):
    ctxt = super().get_context_data(**kwargs)
    items = Item.objects.all().order_by("-dt_closed")
    items_upcoming = []
    items_live = []
    items_closed = []
    for item in items:
      item.additional_winners = item.additional_winners()
      if item.live:
        items_live.append(item)
      elif item.closed:
        items_closed.append(item)
      else:
        items_upcoming.append(item)
    ctxt["items_upcoming"] = items_upcoming
    ctxt["items_live"] = items_live
    ctxt["items_closed"] = items_closed
    return ctxt


# Called by ajax.
def update_bids(request):
  items = Item.objects.all()
  item_updates = {}
  for item in items:
    if item.status != "upcoming":
      item_updates[item.id] = {"status": item.status, "winning_price": item.formatted_winning_price, "winning_name": item.winning_name, "additional_winners": item.additional_winners()}
      if item.status == "live":
        item_updates[item.id]["dt_closed"] = item.dt_closed.strftime("%d-%m-%Y %H:%M")
        item_updates[item.id]["remaining"] = item.time_until_close()
  return JsonResponse({'item_updates': item_updates})


# Called by ajax.
def add_bid(request, item_id, price, name, phone_number):
  item = get_object_or_404(Item, id=item_id)
  error = ""
  try:
    price = float(price)
  except:
    return JsonResponse({"error": "Your bid must be a number! What are you playing at? O.o"})
  if item.status != "live":
    if item.status == "unopened":
      error = "This item has not yet gone live. How did you even get here? :/"
    else:
      error = "This item is no longer live. Sorry about that. :("
  elif item.winning_price:
    if item.winners_num == 1:
      if price <= item.winning_price:
        error = "Your bid must be higher than the current winning bid (£" + item.formatted_winning_price + ")."
      elif item.winning_name == name and item.winning_phone_number == phone_number:
        error = "You're already winning this item - no need to outbid yourself!"
    elif item.winners_num > 1:
      lowest_winning_price = item.lowest_winning_price()
      highest_user_price = item.highest_user_price(name, phone_number)
      if price <= lowest_winning_price:
        error = "Your bid must be higher than the current lowest winning bid (£" + '{:0,.2f}'.format(lowest_winning_price) + ")."
      elif price <= highest_user_price:
        error = "Your bid must be higher than your previous bid (£" + '{:0,.2f}'.format(highest_user_price) + ")."
  elif price < item.base_price:
    error = "You bid must be higher than base price (£" + item.formatted_base_price + ")."
  if error == "":
    Bid.objects.create(item=item, name=name, price=price, phone_number=phone_number)
    if not item.winning_price or price > item.winning_price:
      item.winning_price = price
      item.winning_name = name
      item.winning_phone_number = phone_number
      item.save()
  return JsonResponse({'error': error})


class MessageGeneratorView(AuctionSettingMixin, generic.TemplateView):
  template_name = 'message_generator.html'
