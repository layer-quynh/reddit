import random
import time
from functools import wraps

import redis
from django.test import Client
from django.test import TransactionTestCase

from backend.cron import update_total_comments
from backend.models import Post, Comment
from config import host


class PostTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        redis_client = None
        try:
            redis_client = redis.Redis(host=host, port=6379, db=0, charset="utf-8", decode_responses=True)
        except Exception:
            pass

        for key in redis_client.keys():
            redis_client.delete(key)

        for i in range(20):
            self.client.post('/api/v1/posts',
                             {'body': f'Post {i}'}, 'application/json')

        def create_comment(post_id, parent_id):
            data = {'body': f'New comment of post {post_id}'}
            if parent_id != '':
                data['parent_id'] = parent_id

            response = self.client.post(f'/api/v1/posts/{post_id}/comments',
                                        data, 'application/json')
            return response.json()['id']

        # Post with id 10, 11, 15 have 10 comments
        for i in [10, 11, 15]:
            previous_comment = None
            for j in range(10):
                previous_comment = create_comment(i, previous_comment)

        # Post with id 8, 9, 19 have 5 comments
        for i in [8, 9, 19]:
            previous_comment = None
            for j in range(5):
                previous_comment = create_comment(i, previous_comment)

        # Post with id 1, 2, 3, 4 have 3 comments
        for i in [1, 2, 3, 4]:
            previous_comment = None
            for j in range(3):
                previous_comment = create_comment(i, previous_comment)

    def test_get_top(self):
        response = self.client.get('/api/v1/posts')
        list_post = [post['id'] for post in response.json()['results']]
        self.assertEqual(set(list_post), {15, 11, 10, 9, 8, 19, 1, 4, 3, 2})
        self.assertEqual(response.status_code, 200)

    # return all if we want to get more than number of records in DB
    def test_get_top_20(self):
        response = self.client.get('/api/v1/posts?limit=20')
        list_post = [post['id'] for post in response.json()['results']]
        self.assertEqual(set(list_post), {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20})
        self.assertEqual(response.status_code, 200)

    def test_get_top_3(self):
        response = self.client.get('/api/v1/posts?limit=3')
        list_post = [post['id'] for post in response.json()['results']]
        self.assertEqual(set(list_post), {15, 11, 10})
        self.assertEqual(response.status_code, 200)

    def test_get_top_6(self):
        response = self.client.get('/api/v1/posts?limit=6')
        list_post = [post['id'] for post in response.json()['results']]
        self.assertEqual(set(list_post), {15, 11, 10, 9, 8, 19})
        self.assertEqual(response.status_code, 200)

    def test_get_post(self):
        response = self.client.get('/api/v1/posts/10')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['body'], 'Post 9')
        self.assertEqual(len(response.json()['comments']), 10)

        response = self.client.get('/api/v1/posts/19')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['body'], 'Post 18')
        self.assertEqual(len(response.json()['comments']), 5)

        response = self.client.get('/api/v1/posts/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['body'], 'Post 0')
        self.assertEqual(len(response.json()['comments']), 3)

        self.assertEqual(Post.objects.count(), 20)

    def test_get_post_not_exist(self):
        response = self.client.get('/api/v1/posts/100')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Post.objects.count(), 20)

    def test_create_post(self):
        response = self.client.post('/api/v1/posts',
                                    {'body': 'New created post'},
                                    'application/json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['body'], 'New created post')
        self.assertEqual(Post.objects.count(), 21)


class CommentTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.client = Client()
        Post.objects.create(body='Post 1', id=1)
        Post.objects.create(body='Post 2', id=2)

    def test_create_comment(self):
        self.client.post('/api/v1/posts/1/comments',
                         {'body': 'Comment 1'},
                         'application/json')
        self.client.post('/api/v1/posts/1/comments',
                         {'body': 'Comment 2', 'parent_id': 1},
                         'application/json')
        self.client.post('/api/v1/posts/1/comments',
                         {'body': 'Comment 3', 'parent_id': 2},
                         'application/json')
        self.assertEqual(Comment.objects.count(), 3)

        self.client.post('/api/v1/posts/2/comments',
                         {'body': 'Comment 4'},
                         'application/json')
        self.client.post('/api/v1/posts/2/comments',
                         {'body': 'Comment 5', 'parent_id': 4},
                         'application/json')
        self.assertEqual(Comment.objects.count(), 5)

        response = self.client.post('/api/v1/posts/2/comments',
                                    {'body': 'Comment 6', 'parent_id': 5},
                                    'application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['body'], 'Comment 6')
        self.assertEqual(response.json()['path'], '/4/5')
        self.assertEqual(response.json()['post'], 2)

        response = self.client.post('/api/v1/posts/1/comments',
                                    {'body': 'Comment 7', 'parent_id': 3},
                                    'application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['body'], 'Comment 7')
        self.assertEqual(response.json()['path'], '/1/2/3')
        self.assertEqual(response.json()['post'], 1)

    def test_get_comment(self):
        self.client.post('/api/v1/posts/1/comments',
                         {'body': 'Comment 1'},
                         'application/json')
        response = self.client.get('/api/v1/posts/1/comments/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['body'], 'Comment 1')
        self.assertEqual(response.json()[0]['path'], '')

        self.client.post('/api/v1/posts/1/comments',
                         {'body': 'Comment 2', 'parent_id': 1},
                         'application/json')
        response = self.client.get('/api/v1/posts/1/comments/2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['body'], 'Comment 2')
        self.assertEqual(response.json()[0]['path'], '/1')

    # comment is not existed
    def test_get_comment_not_existed(self):
        response = self.client.get('/api/v1/posts/1/comments/1')
        self.assertEqual(response.status_code, 404)

        self.client.post('/api/v1/posts/1/comments',
                         {'body': 'Comment 1'},
                         'application/json')

        response = self.client.get('/api/v1/posts/2/comments/1')
        self.assertEqual(response.status_code, 404)

    # post is not existed
    def test_post_comment_without_post(self):
        response = self.client.post('/api/v1/posts/3/comments',
                                    {'body': 'Comment 1'},
                                    'application/json')
        self.assertEqual(response.status_code, 404)

    # post is existed, but parent comment is not -> make it as a base comment
    def test_post_comment_without_parent(self):
        response = self.client.post('/api/v1/posts/2/comments',
                                    {'body': 'Comment 9'},
                                    'application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['body'], 'Comment 9')
        self.assertEqual(response.json()['path'], '')
        self.assertEqual(response.json()['post'], 2)


def time_measured(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        print(f'Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds')
        return result

    return timeit_wrapper


class StressTestCase(TransactionTestCase):
    def setUp(self):
        redis_client = None
        try:
            redis_client = redis.Redis(host=host, port=6379, db=0, charset="utf-8", decode_responses=True)
        except Exception:
            pass

        for key in redis_client.keys():
            redis_client.delete(key)

    @time_measured
    def generate(self, num_post, num_comment):
        for i in range(num_post):
            self.client.post('/api/v1/posts',
                             {'body': 'New post'},
                             'application/json')

            comment_ids = [-1]
            post_id = i + 1

            delta = random.randrange(-num_comment // 5, num_comment // 5)
            for j in range(num_comment + delta):
                parent_id = random.choice(comment_ids)
                if parent_id == -1:
                    self.client.post(f'/api/v1/posts/{post_id}/comments',
                                     {'body': 'New comment'},
                                     'application/json')
                else:
                    self.client.post(f'/api/v1/posts/{post_id}/comments',
                                     {'body': 'New comment', 'parent_id': parent_id},
                                     'application/json')

    @time_measured
    def get_top(self):
        response = self.client.get('/api/v1/posts')
        list_post = [post['id'] for post in response.json()['results']]
        return list_post

    def test_stress(self):
        self.generate(100000, 150)
        top_posts = self.get_top()
        update_total_comments()
        validation_top_posts = [post.id for post in Post.objects.order_by('-total_comments').all()[:10]]
        self.assertEqual(set(top_posts), set(validation_top_posts))
