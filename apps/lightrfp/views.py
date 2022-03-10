import twilio.twiml
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from carton.cart import Cart
from users.models import User
from vendors.models import Vendor
from vendors.models import RFP, Bid
from .forms import RFPForm, MessageForm, BidForm, RFPNotificationSettingsForm
from .utils import buy_masked_phone


@transaction.atomic
def bid_list(request, username):
    user = get_object_or_404(User, username=username)
    cart = Cart(request.session)
    shortlist = Vendor.objects.none()
    if cart.products:
        shortlist = Vendor.objects.filter(pk__in=map(lambda x: x.pk, cart.products))

    if request.method == 'POST':
        if 'join' in request.POST:
            rfp = get_object_or_404(RFP, uuid=request.POST['rfp'])
            vendor = user.vendors.filter(categories__rfps=rfp)[0]  # TODO: need to be able to specify which vendor will join
            bid = Bid.objects.get_or_create(rfp=rfp, vendor=vendor)
            messages.success(request, 'Joined RFP.')
            return redirect('bid_view', user.username, bid.uuid)
        else:
            form = RFPForm(request.POST, client=user, shortlist=shortlist)
            if form.is_valid():
                rfp = form.save(commit=False)
                rfp.client = user
                rfp.save()
                if form.cleaned_data['phone'] != user.phone:
                    user.phone = form.cleaned_data['phone']
                    user.save()
                if rfp.masked and not rfp.masked_phone:
                    rfp.masked_phone = buy_masked_phone()
                    rfp.save()
                for vendor in form.cleaned_data['vendors']:
                    Bid.objects.get_or_create(rfp=rfp, vendor=vendor)
                for bid in rfp.bids.all():
                    if bid.vendor not in form.cleaned_data['vendors']:
                        bid.delete()  # TODO/FIXME: potentially dangerous
                for category in form.cleaned_data['categories']:
                    rfp.categories.add(category)
                messages.success(request, 'RFP created.')
                return redirect('bid_list', user.username)
    else:
        form = RFPForm(client=user, shortlist=shortlist)

    rfps_out = RFP.objects.filter(client=user)
    bids_in = Bid.objects.filter(vendor__users=user)
    open_rfps = RFP.objects.exclude(client=user).exclude(bids__vendor__users=user).filter(categories__vendors__users=user)

    return render(request, 'bid_list.html', {
        'user': user,
        'form': form,
        'rfps_out': rfps_out,
        'bids_in': bids_in,
        'open_rfps': open_rfps,
    })


@transaction.atomic
def rfp_edit(request, username, uuid):
    user = get_object_or_404(User, username=username)
    rfp = get_object_or_404(RFP, client=user, uuid=uuid)

    if request.method == 'POST':
        form = RFPForm(request.POST, instance=rfp, client=user)
        if form.is_valid():
            rfp = form.save(commit=False)
            rfp.client = user
            rfp.save()
            if form.cleaned_data['phone'] != user.phone:
                user.phone = form.cleaned_data['phone']
                user.save()
            if rfp.masked and not rfp.masked_phone:
                rfp.masked_phone = buy_masked_phone()
                rfp.save()
            for vendor in form.cleaned_data['vendors']:
                Bid.objects.get_or_create(rfp=rfp, vendor=vendor)
            for bid in rfp.bids.all():
                if bid.vendor not in form.cleaned_data['vendors']:
                    bid.delete()  # TODO/FIXME: potentially dangerous
            for category in form.cleaned_data['categories']:
                rfp.categories.add(category)
            messages.success(request, 'Request updated.')
            return redirect('rfp_view', user.username, rfp.uuid)
    else:
        form = RFPForm(instance=rfp, client=user)

    return render(request, 'rfp_edit.html', {'user': user, 'rfp': rfp, 'form': form})


@transaction.atomic
def rfp_view(request, username, uuid, bid_uuid=None):
    user = get_object_or_404(User, username=username)
    rfp = get_object_or_404(RFP, client=user, uuid=uuid)
    bid = get_object_or_404(Bid, rfp=rfp, uuid=bid_uuid) if bid_uuid else None
    if bid_uuid is None:
        bid = rfp.bids.first()

    if request.method == 'POST':
        if 'winner' in request.POST:
            bid = Bid.objects.get(uuid=request.POST['rfp_bid'])
            bid.winner = not bid.winner
            bid.save()
            if bid.winner:
                rfp.bids.exclude(pk=bid.pk).update(winner=False)
            messages.success(request, 'Selected winner.')
            return redirect('rfp_view', user.username, rfp.uuid, bid.uuid)
        elif 'notif' in request.POST:
            notif_form = RFPNotificationSettingsForm(request.POST, instance=rfp)
            form = MessageForm()
            if notif_form.is_valid():
                rfp = notif_form.save()
                messages.success(request, 'Notification settings updated.')
                return redirect('rfp_view', user.username, rfp.uuid)
        else:
            form = MessageForm(request.POST)
            notif = RFPNotificationSettingsForm(instance=rfp)
            if form.is_valid():
                msg = form.save(commit=False)
                msg.bid = Bid.objects.get(uuid=request.POST['rfp_bid'])
                msg.sender = user
                msg.save()
                messages.success(request, 'Message sent.')
                return redirect('rfp_view', user.username, rfp.uuid, msg.bid.uuid)
    else:
        form = MessageForm()
        notif_form = RFPNotificationSettingsForm(instance=rfp)

    return render(request, 'rfp_view.html', {'user': user, 'rfp': rfp, 'form': form, 'bid': bid, 'notif_form': notif_form})


@transaction.atomic
def bid_view(request, username, uuid):
    user = get_object_or_404(User, username=username)
    bid = get_object_or_404(Bid.filter_by_user(user), uuid=uuid)

    if request.method == 'POST':
        if 'winner' in request.POST:
            bid.winner = not bid.winner
            bid.save()
            if bid.winner:
                bid.rfp.bids.exclude(pk=bid.pk).update(winner=False)
            messages.success(request, 'Selected winner.')
            return redirect('bid_view', user.username, bid.uuid)
        elif 'bid_form' in request.POST:
            bid_form = BidForm(request.POST, instance=bid)
            form = MessageForm()
            if bid_form.is_valid():
                bid = bid_form.save()
                messages.success(request, 'Bid updated.')
                return redirect('bid_view', user.username, bid.uuid)
        elif 'c2c' in request.POST:
            if bid.rfp.notif_call:
                if bid.rfp.masked_phone:
                    bid.masked_phone = bid.rfp.masked_phone  # buy_masked_phone()
                    bid.save()
                    messages.success(request, 'Phone number generated. Call that number to reach the client.')
                    return redirect('bid_view', user.username, bid.uuid)
                elif bid.rfp.client.phone:
                    bid.masked_phone = bid.rfp.client.phone
                    bid.save()
                    messages.success(request, 'Phone number generated. Call that number to reach the client.')
                    return redirect('bid_view', user.username, bid.uuid)
            messages.warning(request, 'The client cannot be called.')
            return redirect('bid_view', user.username, bid.uuid)
        else:
            form = MessageForm(request.POST)
            bid_form = BidForm(instance=bid)
            if form.is_valid():
                msg = form.save(commit=False)
                msg.bid = bid
                msg.sender = user
                msg.save()
                messages.success(request, 'Message sent.')
                return redirect('bid_view', user.username, bid.uuid)
    else:
        form = MessageForm()
        bid_form = BidForm(instance=bid)
        notif_form = RFPNotificationSettingsForm(instance=bid.rfp)

    return render(request, 'bid_view.html', {'user': user, 'bid': bid, 'form': form, 'bid_form': bid_form, 'notif_form': notif_form})


@csrf_exempt
def twilio_voice(request):
    if request.method == 'POST':
        try:
            bid = Bid.objects.get(
                vendor__users__phone=request.POST.get('From'),
                masked_phone=request.POST.get('To'),
            )
            if bid.rfp.notif_call and bid.rfp.client.phone:
                bid.messages.create(message='{} started a call.'.format(bid.vendor))
                # bid.masked_phone = ''
                # bid.save()

                response = twilio.twiml.Response()
                response.addDial(str(bid.rfp.client.phone))
                return HttpResponse(str(response), content_type='text/xml')
        except Bid.DoesNotExist:
            pass

    response = twilio.twiml.Response()
    response.addSay('Thanks for using Proven. For privacy reasons, this number can only be used once. Please use the Click to Call button online. Thank you!')
    return HttpResponse(str(response), content_type='text/xml')
