from django.shortcuts import render, redirect, get_object_or_404
from .models import Entry, Category
from .forms import EntryForm, RegisterForm
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.contrib.auth import login
import csv


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = RegisterForm()

    return render(request, 'journal/register.html', {'form': form})


@login_required
def dashboard(request):
    entries = Entry.objects.filter(user=request.user).order_by('-created_at')
    total_entries = entries.count()

    category_data = entries.values('category__name').annotate(count=Count('id'))

    monthly_counts_qs = (
        entries.annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    monthly_counts = {
        item['month'].strftime('%Y-%m'): item['count']
        for item in monthly_counts_qs if item['month']
    }

    type_data = entries.values('entry_type').annotate(count=Count('id'))

    dates = [e.created_at.date() for e in entries]
    streak = 0
    if dates:
        unique_dates = sorted(set(dates))
        current_streak = 1
        max_streak = 1

        for i in range(1, len(unique_dates)):
            if (unique_dates[i] - unique_dates[i - 1]).days == 1:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1

        streak = max_streak

    context = {
        'entries': entries[:4],
        'total_entries': total_entries,
        'category_data': category_data,
        'monthly_counts': monthly_counts,
        'type_data': type_data,
        'streak': streak,
    }

    return render(request, 'journal/dashboard.html', context)


@login_required
def add_entry(request):
    if request.method == 'POST':
        form = EntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()
            form.save_m2m()
            return redirect('dashboard')
        else:
            print(form.errors)   # debug
    else:
        form = EntryForm()

    return render(request, 'journal/add_entry.html', {'form': form})


@login_required
def all_entries(request):
    entries = Entry.objects.filter(user=request.user).order_by('-created_at')
    categories = Category.objects.all()

    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    entry_type = request.GET.get('type', '').strip()

    if query:
        entries = entries.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    if category:
        entries = entries.filter(category__id=category)

    if entry_type:
        entries = entries.filter(entry_type=entry_type)

    context = {
        'entries': entries,
        'categories': categories,
        'selected_category': category,
        'selected_type': entry_type,
        'search_query': query,
    }

    return render(request, 'journal/all_entries.html', context)


@login_required
def edit_entry(request, entry_id):
    entry = get_object_or_404(Entry, id=entry_id, user=request.user)

    if request.method == 'POST':
        form = EntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            return redirect('all_entries')
    else:
        form = EntryForm(instance=entry)

    return render(request, 'journal/edit_entry.html', {'form': form, 'entry': entry})


@login_required
def delete_entry(request, entry_id):
    entry = get_object_or_404(Entry, id=entry_id, user=request.user)

    if request.method == 'POST':
        entry.delete()
        return redirect('all_entries')

    return render(request, 'journal/delete_entry.html', {'entry': entry})


@login_required
def export_csv(request):
    entries = Entry.objects.filter(user=request.user)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="curiosity_entries.csv"'

    writer = csv.writer(response)
    writer.writerow(['Title', 'Description', 'Category', 'Type', 'Tags', 'Created At'])

    for entry in entries:
        tags = ', '.join([tag.name for tag in entry.tags.all()])
        writer.writerow([
            entry.title,
            entry.description,
            entry.category.name if entry.category else '',
            entry.entry_type,
            tags,
            entry.created_at
        ])

    return response