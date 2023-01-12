# Python Test 

## Requirements

### Techinal requirements

Using Python 3.x & Django or FastAPI. We will build a simple Reddit-style discussion API .

We have several question types for our professors to support their in-class activities. We would like to add another question type called a discussion question. As a MVP we would like to develop a functionality for the professor to start a discussion and students can respond to a question with their comments. Students can also respond to each other’s comments. 


### Example

1. The professor starts a discussion by asking `How is your day going so far?`;
2. One student responds with `It is going great, Thanks!`;
3. Another student responds to the professor by saying `Unfortunately, I had a bad day!` and another student responds to that student’s comment by saying `Oh no! Sorry to hear that. What happened?`;
4. The response chain can go on and on;
5. The professor can also start a new discussion by asking `What do we want to learn today?`.

### Detailed requirements

With this example in mind, we would like to build API(s) so that:
- Any user can start a new discussion.
- Any user can respond to a discussion or comment.
- Any user can retrieve all the comments available in the database in a flat tree for a given discussion. 
- Return top 10 hot discussion (have most comments) 

Try to generate 100,000 dummy records and check the time to return the top 10 hot discussions. Could you try some technique to reduce the processing time ? 

You should write unit tests to validate the correctness of this API.

## Things that are out of scope for building this API
There won’t be any user authentication layer. Any user should be able to create a new discussion and respond to other discussions.

## General instructions
You can choose to work with any backend language and framework that you feel comfortable with.
Please include API documentation that explains URL structure and API response schema
Upon completion of this exercise, please provide us with your source code and step-by-step instructions on how to deploy and run the application. To send us the code, you can either:
Provide us with access to your private GitHub repository.
Or you can compress your code and send us the zip file.

## Solution

### Technical requirements

- Python: version `3.8`
- Django: version `4.1.5`
- Postgres: version `12`
- Redis: version `4.4.1`

### APIs

1. `GET /api/v1/posts/<id>`

Return post with specific `id` and its comments.

2. `GET /api/v1/posts?limit=<limit>`

Return `<limit>` posts with most comments.

3. `POST /api/v1/posts`

    ```json
    {
      "body": "Example post"
    }
    ```

Create a new post.

4. `POST /api/v1/posts/<post_id>/comments`

    ```json
    {
      "body": "Example",
      "parent_id": 1
    }
    ```
Create a new comment with parent is comment with `parent_id` and in
post `post_id`. In case there are not `parent_id`, then it is a direct
comment of the post.

### Design database

#### Post

- `id`: Post's id.
- `created_at`: Audit field to clarify when post was created.
- `body`: Post's content.
- `total_comments`: Number of comments in a post. We will update this
field every 10 minutes as a background task using cron job.

#### Comment

- `id`: Comment's id.
- `created_at`: Audit field to clarify when comment was created.
- `body`: Comment's content.
- `path`: The traverse path of comment's hierarchy. Using this
field we could trace back all the parent comments. It also
helps us find out all the child comments.
- `post`: ID of post, which the comment is belonged to.

### Optimization

**1. Calculate total comments**

We will use a Redis instance to keep track the number of comments
in a post. The reason why I don't directly updating the `Post`
table is because it is an expensive and heavy operation. Especially is when
users create a lot of comments, if for every created comment, we
have to write back to the database, then it will be extremely 
expensive.

Therefor, I use and Redis to store `<post_id, total_comments>`
to rapidly update and read total comments of posts. Then I use
cronjob to update the database every 10 minutes to synchronous the 
data.

**2. Finding nested comments**

Using `path` with index, we could quickly find all the child
comments of a comments. Because we only need to find the prefix 
of `path`.