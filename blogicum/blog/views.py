from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from .constants import NUMBER_OF_PUBLICATIONS
from .forms import CommentForm, PostForm, UserForm
from .models import Category, Comment, Post, User


class PostReverseMixin:

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']},
        )


class ProfileReverseMixin:

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            args=[self.request.user],
        )


class PostMixin:
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=kwargs['post_id'])
        if post.author != request.user:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)


class CommentMixin:
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, pk=kwargs['comment_id'])
        if comment.author != request.user:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)


class IndexListView(ListView):
    queryset = Post.manager.all()
    template_name = 'blog/index.html'
    paginate_by = NUMBER_OF_PUBLICATIONS


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(Post, id=kwargs['post_id'])
        if post.author == request.user or (
            post.is_published and post.pub_date <= timezone.now()
            and post.category.is_published
        ):
            return super().dispatch(request, *args, **kwargs)
        raise Http404('Post not found')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context


class CategoryPostsListView(ListView):
    template_name = 'blog/category.html'
    paginate_by = NUMBER_OF_PUBLICATIONS

    def get_queryset(self):
        return Post.manager.filter(
            category__slug=self.kwargs['category_slug'],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True,
        )
        return context


class ProfileListView(ListView):
    model = User
    template_name = 'blog/profile.html'
    paginate_by = NUMBER_OF_PUBLICATIONS

    def get_queryset(self):
        posts = Post.objects.select_related(
            'category',
            'author',
            'location',
        ).filter(
            author__username=self.kwargs['username'],
        ).order_by(
            '-pub_date',
        ).annotate(
            comment_count=Count('comments'),
        )
        if self.request.user.username != self.kwargs['username']:
            posts = posts.filter(
                is_published=True,
                category__is_published=True,
                pub_date__lt=timezone.now(),
            )
        return posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User,
            username=self.kwargs['username'],
        )
        return context


class ProfileUpdateView(ProfileReverseMixin, LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def dispatch(self, request, *args, **kwargs):
        get_object_or_404(
            User,
            id=request.user.pk,
        )
        return super().dispatch(request, *args, **kwargs)


class PostCreateView(ProfileReverseMixin, LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(
    PostMixin,
    PostReverseMixin,
    LoginRequiredMixin,
    UpdateView
):
    form_class = PostForm


class PostDeleteView(
    PostMixin,
    ProfileReverseMixin,
    LoginRequiredMixin,
    DeleteView
):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context


class CommentCreateView(PostReverseMixin, LoginRequiredMixin, CreateView):
    comment = None
    model = Comment
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        self.comment = get_object_or_404(Post, pk=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.comment
        return super().form_valid(form)


class CommentUpdateView(
    CommentMixin,
    PostReverseMixin,
    LoginRequiredMixin,
    UpdateView
):
    pass


class CommentDeleteView(
    CommentMixin,
    PostReverseMixin,
    LoginRequiredMixin,
    DeleteView
):
    pass
