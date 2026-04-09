from django.shortcuts import render, redirect
from .models import Entry
from .forms import EntryForm
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
import csv
from collections import Counter


@login_required
def dashboard(request):
    entries = Entry.objects.filter(user=request.user).order_by('-created_at')
    total_entries = entries.count()

    # Category chart data
    category_data = entries.values('category__name').annotate(count=Count('id'))

    # Monthly chart data
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

    # Entry type chart
    type_data = entries.values('entry_type').annotate(count=Count('id'))

    # Heatmap / daily activity data
    dates = [e.created_at.date() for e in entries]
    heatmap_counts = Counter(dates)

    # Streak logic
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
        'entries': entries[:5],  # latest 5 entries
        'total_entries': total_entries,
        'category_data': category_data,
        'monthly_counts': monthly_counts,
        'type_data': type_data,
        'heatmap_counts': heatmap_counts,
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
        form = EntryForm()

    return render(request, 'journal/add_entry.html', {'form': form})


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