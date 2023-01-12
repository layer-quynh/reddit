import json

import redis
from rest_framework.generics import GenericAPIView, ListCreateAPIView
from rest_framework.response import Response

from backend.models import Post, Comment
from backend.serializers import PostsSerializer, PostSerializer, CommentPostSerializer, CommentGetSerializer
from config import *

redis_client = None
try:
    redis_client = redis.Redis(host=host, port=6379, db=0, charset="utf-8", decode_responses=True)
except Exception:
    pass


class PostsView(ListCreateAPIView):
    authentication_classes = ()
    serializer_class = PostsSerializer

    """
    Get top hot posts
    """

    def get_queryset(self):
        get_items = self.request.GET
        limit = get_items.get('limit')

        if limit is not None:
            limit = int(limit) - 1

        """
        Get list ids from redis
        """
        try:
            top_posts = redis_client.zrange('comments', 0, limit - 1, desc=True, withscores=True)
        except (redis.exceptions.ConnectionError,
                redis.exceptions.BusyLoadingError):
            top_posts = []

        """
        If list_comment_ids exists in redis, query list comments from list_comment_ids in posts table.
        Else, query directly from posts table
        """
        if len(top_posts):
            for post_id, total_comments in top_posts:
                Post.objects.filter(id=post_id).update(total_comments=total_comments)
            return Post.objects.filter(id__in=[post_id for post_id, total_comments in top_posts]). \
                order_by('-total_comments')

        return Post.objects.order_by('-total_comments')

    """
    Create new post
    """

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        serializer = PostSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response = serializer.data

        """
        Add total_comments of new post to redis
        """
        try:
            redis_client.zadd('comments', {str(response['id']): 0})
        except (redis.exceptions.ConnectionError,
                redis.exceptions.BusyLoadingError):
            pass

        return Response(response, status=201)


class PostView(GenericAPIView):
    authentication_classes = ()

    """
    Get a post by its id
    """

    def get(self, request, post_id):
        post = Post.objects.filter(id=post_id).first()

        if post is None:
            return Response(data={'code': 'not_found', 'message': 'Post not found'}, status=404)
        post_serializer = PostSerializer(instance=post)
        res = post_serializer.data

        return Response(res)


class CommentsView(ListCreateAPIView):
    authentication_classes = ()
    serializer_class = CommentPostSerializer

    """
    Custom get query set for comments
    """

    def get_queryset(self):
        post_id = self.kwargs.get('post_id')

        return Comment.objects. \
            filter(post_id=post_id). \
            order_by('-created_at')

    """
    Create new comment for a post
    """

    def post(self, request, post_id):
        post = Post.objects.filter(id=post_id).first()

        if post is None:
            return Response(data={'code': 'post_not_found',
                                  'message': 'Post not found'}, status=404)
        data = json.loads(request.body)
        data['post'] = post_id
        parent_id = data.get('parent_id', None)

        # Update path from parent comment
        if parent_id is not None:
            parent_comment = self.get_queryset().filter(id=parent_id).first()
            if parent_comment is not None:
                data['path'] = f'{parent_comment.path}/{parent_id}'

        serializer = CommentGetSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        """
        Get total comments value of post id from Redis
        """
        try:
            total_comments = redis_client.zscore('comments', str(post.id))
        except (redis.exceptions.ConnectionError,
                redis.exceptions.BusyLoadingError):
            total_comments = Comment.objects.filter(post_id=post_id).count()

        """
        If value of total comments in redis is None, count it from db
        Else increase total comment with 1
        """
        if total_comments is None:
            total_comments = Comment.objects.filter(post_id=post_id).count()
        else:
            total_comments = int(total_comments) + 1

        """
        Update total comments value in redis
        """
        try:
            redis_client.zadd('comments', {str(post.id): total_comments})
        except (redis.exceptions.ConnectionError,
                redis.exceptions.BusyLoadingError):
            Post.objects.filter(id=post_id).update(total_comments=total_comments)

        response = serializer.data

        return Response(response, status=201)


class NestedCommentsView(GenericAPIView):
    authentication_classes = ()

    """
    Custom get query set for comments
    """

    def get_queryset(self):
        post_id = self.kwargs.get('post_id')

        return Comment.objects. \
            filter(post_id=post_id). \
            order_by('-created_at')

    def get(self, request, post_id, comment_id):
        post = Post.objects.filter(id=post_id).first()

        if post is None:
            return Response(data={'code': 'post_not_found',
                                  'message': 'Post not found'}, status=404)

        comment = self.get_queryset().filter(id=comment_id).first()

        if comment is None:
            return Response(data={'code': 'comment_not_found',
                                  'message': 'Comment not found'}, status=404)

        child_path = f'{comment.path}/{comment_id}'
        response = [
            CommentGetSerializer(comment).data for comment in Comment.objects.filter(path__startswith=child_path)[::1]
        ]
        response.insert(0, CommentGetSerializer(comment).data)
        response = Response(response)

        return response
