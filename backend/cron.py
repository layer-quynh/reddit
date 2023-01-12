from django.db import connection

"""
This function runs every 10 minutes to update total comments in posts table
"""


def update_total_comments():
    with connection.cursor() as cursor:
        query = "UPDATE public.posts p SET total_comments = c.total_comments from (select count(id) as total_comments, " \
                "post_id from public.comments group by post_id) c where p.id = c.post_id"
        cursor.execute(query)
