from django.shortcuts import render, get_object_or_404
from .models import Post


def post_list(request):
    posts = Post.objects.all()
    return render(request, 'posts/list.html', {'posts': posts})


def post_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'posts/view.html', {'post': post})
