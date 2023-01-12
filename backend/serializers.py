from rest_framework import serializers

from backend.models import Post, Comment


class CommentPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        exclude = ['post']


class CommentGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'


# Serializer for comments nested in a post
class NestedCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        exclude = ['post']
        ordering = ['-created_at']


# Serializer for posts list view
class PostsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'


# Serializer for detail view of post
class PostSerializer(serializers.ModelSerializer):
    comments = NestedCommentSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        exclude = ['total_comments']
