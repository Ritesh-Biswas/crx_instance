from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import BlogPost, PollVote
from comment.models import Comment
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator

@staff_member_required
def blog_stats_view(request):
    # Get time ranges
    now = timezone.now()
    last_week = now - timedelta(days=7)
    last_month = now - timedelta(days=30)

    # Get all posts
    all_posts = BlogPost.objects.all()
    
    # Get top posts by engagement
    top_posts = sorted(all_posts, key=lambda x: x.engagement_score, reverse=True)
    paginator = Paginator(top_posts, 5)  # Show 5 posts per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get post type distribution
    post_types = all_posts.values('post_type').annotate(
        count=Count('id')
    )
    
    # Get recent activity
    recent_posts = all_posts.filter(created_at__gte=last_week).count()
    
    # Get recent likes (modified query)
    recent_likes = all_posts.filter(created_at__gte=last_week).aggregate(
        total_likes=Count('likes')
    )['total_likes']
    
    # Get recent comments
    blog_content_type = ContentType.objects.get_for_model(BlogPost)
    recent_comments = Comment.objects.filter(
        content_type=blog_content_type,
        posted__gte=last_week
    ).count()

    # Get monthly stats
    monthly_posts = all_posts.filter(created_at__gte=last_month).count()
    monthly_likes = all_posts.filter(created_at__gte=last_month).aggregate(
        total_likes=Count('likes')
    )['total_likes']
    monthly_comments = Comment.objects.filter(
        content_type=blog_content_type,
        posted__gte=last_month
    ).count()

    # Get poll stats
    poll_posts = all_posts.filter(post_type='poll')
    total_votes = sum(post.total_votes for post in poll_posts)
    active_polls = sum(1 for post in poll_posts if post.is_poll_active)

    context = {
        'top_posts': top_posts,
         'page_obj': page_obj,
        'post_types': post_types,
        'total_posts': all_posts.count(),
        'recent_posts': recent_posts,
        'recent_likes': recent_likes,
        'recent_comments': recent_comments,
        'monthly_posts': monthly_posts,
        'monthly_likes': monthly_likes,
        'monthly_comments': monthly_comments,
        'total_votes': total_votes,
        'active_polls': active_polls,
    }
    
    return render(request, 'wagtailadmin/blog_stats.html', context)
