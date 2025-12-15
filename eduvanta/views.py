from django.shortcuts import render

def home(request):
    return render(request, 'index.html')  # Render the homepage template, assuming it exists from memories
