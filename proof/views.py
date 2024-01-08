from django.shortcuts import get_object_or_404
from .models import Poste, Relation, Vote, Directs
from django.contrib import messages
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from proof.serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

User = get_user_model()


class CurrentUserView(APIView):
    def get(self, request):
        current_user = request.user

        if not current_user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = UserSerializer(current_user)

        return Response(serializer.data)


class ListPostsView(APIView):
    def get(self, request, username):
        user = User.objects.get(username=username)
        posts = Poste.objects.filter(user=user)
        serialized_posts = PosteSerializer(instance=posts, many=True)
        return Response(data=serialized_posts.data, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    """
    API view to retrieve user profile information, posts, and follower count.
    """
    serializer_class = UserSerializer

    def get(self, request, username):
        """
        Handle GET request to retrieve user profile information, posts, and follower count.

        Args:
            request (HttpRequest): The HTTP request object.
            username (str): The username of the user whose profile information is requested.

        Returns:
            Response: The HTTP response containing the serialized user profile, posts, and follower count.

        Raises:
            Http404: If the requested user does not exist.
        """

        user = get_object_or_404(User, username=username)

        posts = Poste.objects.filter(user=user)

        # Check if there is a follower relationship between the user and the current user
        is_followed = False
        if request.user.is_authenticated:
            if Relation.objects.filter(from_user=request.user, to_user=user).exists():
                is_followed = True

        followers = Relation.objects.filter(to_user_id=user.id)
        followers_number = followers.count()

        serialized_user = UserSerializer(instance=user)
        serialized_posts = PosteSerializer(instance=posts, many=True)

        response = {
            "user": serialized_user.data,
            "posts": serialized_posts.data,
            "is_followed": is_followed,
            "followers": followers_number
        }

        # Return the response with the serialized data
        return Response(data=response, status=status.HTTP_200_OK)


class PostDetailView(APIView):
    """
    API view to retrieve post details, comments, likes, and liked status.
    """
    serializer_class = PosteSerializer

    def get(self, request, post_id, post_slug):
        """
        Handle GET request to retrieve post details, comments, likes, and liked status.

        Args:
            request (HttpRequest): The HTTP request object.
            post_id (int): The ID of the post.
            post_slug (str): The slug of the post.

        Returns:
            Response: The HTTP response containing the serialized post details, comments, likes, and liked status.

        Raises:
            Http404: If the requested post does not exist.
        """
        post_instance = get_object_or_404(Poste, id=post_id, slug=post_slug)

        liked = False
        if request.user.is_authenticated:
            if Vote.objects.filter(post=post_instance, user=request.user).exists():
                liked = True

        likes_count = Vote.objects.filter(post=post_instance).count()
        comments = post_instance.pcomments.filter(is_reply=False)

        serialized_comments = CommentShowSerializer(comments, many=True)
        serialized_post = PosteSerializer(post_instance)

        data = {
            "post": serialized_post.data,
            "comments": serialized_comments.data,
            "liked": liked,
            'likes_count': likes_count
        }
        return Response(data=data)


class CommentCreateView(APIView):
    """
    API view to create a new comment for a post.
    """
    serializer_class = CommentCreateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id, post_slug):
        """
        Handle POST request to create a new comment for a post.

        Args:
            request (HttpRequest): The HTTP request object.
            post_id (int): The ID of the post.
            post_slug (str): The slug of the post.

        Returns:
            Response: The HTTP response containing the serialized comment data.

        Raises:
            Http404: If the requested post does not exist.
            Http400: If the requested post data was invalid.

        """

        serializer = CommentCreateSerializer(data=request.data)
        post_instance = get_object_or_404(Poste, id=post_id, slug=post_slug)

        if serializer.is_valid():
            serializer.save(
                user=request.user,
                post=post_instance,
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentDeleteView(APIView):
    """
    API view to delete a comment.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, comment_id):
        """
        Handle DELETE request to delete a comment.

        Args:
            request (HttpRequest): The HTTP request object.
            comment_id (int): The ID of the comment.

        Returns:
            Response: The HTTP response indicating the result of the comment deletion.

        Raises:
            Http404: If the requested comment does not exist.
        """

        comment = get_object_or_404(Comment, id=comment_id)

        if request.user == comment.user:
            comment.delete()
            return Response("Comment deleted successfully", status=status.HTTP_200_OK)
        else:
            return Response("Unauthorized", status=status.HTTP_403_FORBIDDEN)


class PostDeleteView(APIView):
    """
    API view to delete a post.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        """
        Handle DELETE request to delete a post.

        Args:
            request (HttpRequest): The HTTP request object.
            pk (int): The primary key of the post.

        Returns:
            Response: The HTTP response indicating the result of the post deletion.

        Raises:
            Http404: If the requested post does not exist.
        """

        post = get_object_or_404(Poste, pk=pk)

        if post.user != request.user:
            return Response("Unauthorized", status=status.HTTP_403_FORBIDDEN)
        post.delete()
        return Response("Post deleted successfully", status=status.HTTP_200_OK)


class PostUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PosteCreateSerializer

    def put(self, request, post_id):
        post = get_object_or_404(Poste, id=post_id)

        if request.user.id != post.user.id:
            return Response("Unauthorized", status=status.HTTP_403_FORBIDDEN)

        serializer = PosteCreateSerializer(post, request.data, partial=True)

        if serializer.is_valid():
            serializer.save(slug=slugify(serializer.validated_data["body"][:30]))

            return Response("Post updated successfully", status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostCreateView(APIView):
    """
    API view for creating a new post.

    Only authenticated users are allowed to access this view.

    Methods:
        post: Handle the POST request to create a new post.
    """
    serializer_class = PosteCreateSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=PosteCreateSerializer,
    )
    def post(self, request):
        """
        Handle the POST request to create a new post.

        Args:
            request: The HTTP request object.

        Returns:
            A response with the serialized data of the new post and a status code.

        Raises:
            N/A
        """
        serializer = PosteCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                slug=slugify(serializer.validated_data["body"][:30]),
                user=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Follow(APIView):
    """
    API view for following a user.

    Only authenticated users are allowed to access this view.

    Methods:
        post: Handle the POST request to follow a user.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        """
        Handle the POST request to follow a user.

        Args:
            request (rest_framework.request.Request): The request object.
            user_id (int): The ID of the user to follow.

        Returns:
            rest_framework.response.Response: A response indicating the result of the follow operation.
        """
        user = get_object_or_404(User, id=user_id)

        if Relation.objects.filter(from_user=request.user, to_user=user).exists():
            return Response(
                {'detail': 'You are already following this user.'},
                status=status.HTTP_403_FORBIDDEN
            )
        else:
            Relation.objects.create(from_user=request.user, to_user=user)

        return Response(
            {'detail': 'You followed successfully.'},
            status=status.HTTP_201_CREATED
        )


class UnFollow(APIView):
    """
    API view for unfollowing a user.

    Only authenticated users are allowed to access this view.

    Methods:
        post: Handle the POST request to unfollow a user.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        """
        Handle the POST request to unfollow a user.

        Args:
            request (rest_framework.request.Request): The request object.
            user_id (int): The ID of the user to unfollow.

        Returns:
            rest_framework.response.Response: A response indicating the result of the unfollow operation.
        """
        # Retrieve the user to unfollow
        user = get_object_or_404(User, id=user_id)

        # Check if a relation exists between the current user and the user to unfollow
        relation = Relation.objects.filter(
            from_user=request.user, to_user=user)

        if not relation.exists():
            # The user is not being followed
            return Response({'detail': 'You are not following this user.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            # Delete the relation to unfollow the user
            relation.delete()

        # Successfully unfollowed the user
        return Response({'detail': 'Unfollowed successfully.'}, status=status.HTTP_200_OK)


class CommentReplyView(APIView):
    """
    API endpoint for creating a reply to a comment.

    Requires authentication to access.
    """
    PosteCreateSerializer = CommentCreateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id, comment_id):
        """
        Handle HTTP POST request to create a reply to a comment.

        Args:
            request (HttpRequest): The HTTP request object.
            post_id (int): The ID of the parent post.
            comment_id (int): The ID of the parent comment.

        Returns:
            Response: The HTTP response containing the result of the operation.

        Raises:
            Http404: If the parent post or parent comment with the given IDs do not exist.
        """

        post = get_object_or_404(Poste, id=post_id)
        comment = get_object_or_404(Comment, id=comment_id)

        serializer = CommentCreateSerializer(data=request.data)

        if serializer.is_valid() and 'body' in serializer.validated_data:
            # Create a new reply
            serializer.save(
                user=request.user,
                post=post,
                reply=comment,
                is_reply=True,
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostLikeView(APIView):
    """
    API view to like/unlike a post.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        """
        Handle POST request to like/unlike a post.

        Args:
            request (HttpRequest): The HTTP request object.
            post_id (int): The ID of the post.

        Returns:
            Response: The HTTP response indicating the result of the post like/unlike.

        Raises:
            Http404: If the requested post does not exist.
        """

        post = get_object_or_404(Poste, id=post_id)
        like = Vote.objects.filter(post=post, user=request.user)

        if like.exists():
            # Unlike the post
            like.delete()
            return Response({'detail': 'You unliked this post.'}, status=status.HTTP_200_OK)
        else:
            # Like the post
            Vote.objects.create(post=post, user=request.user)
            messages.success(request, 'you liked this post', 'success')
            return Response({'detail': 'You liked this post.'}, status=status.HTTP_201_CREATED)


class UserRelations(APIView):
    """
    API endpoint for retrieving information about a user's followers and following.

    Requires authentication to access.
    """
    PosteCreateSerializer = UserSerializer

    def get(self, request, username):
        """
        Handle HTTP GET request to retrieve information about a user's followers and following.

        Args:
            request (HttpRequest): The HTTP request object.
            username (str): The username of the user.

        Returns:
            Response: The HTTP response containing the user's information, followers, and following.

        Raises:
            Http404: If the user with the given username does not exist.
        """

        user = get_object_or_404(User, username=username)

        followers = user.followers.all()
        following = user.following.all()

        user_serialized = UserSerializer(user)
        followers_serialized = UserSerializer(followers, many=True)
        following_serialized = UserSerializer(following, many=True)

        data = {
            "user": user_serialized.data,
            "followers": followers_serialized.data,
            "following": following_serialized.data
        }

        return Response(data, status=status.HTTP_200_OK)


class EditProfileView(APIView):
    """
    API endpoint for editing a user's profile.

    Requires authentication to access.
    """
    PosteCreateSerializer = UserUpdateSerializer

    def put(self, request, username):
        """
        Handle HTTP POST request to edit the user profile.

        Args:
            request (HttpRequest): The HTTP request object.
            username (str): The username of the user.

        Returns:
            Response: The HTTP response indicating the success or failure of the profile edit.

        Raises:
            Http404: If the user with the given username does not exist.
        """
        user = get_object_or_404(User, username=username)

        if request.user.id != user.id:
            return HttpResponse(status=403)

        serializer = UserUpdateSerializer(instance=user, data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response({'message': 'You edited your profile successfully.', 'data': serializer.data},
                            status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DirectListView(APIView):
    """
    API endpoint for retrieving a list of received and sent direct messages for the authenticated user.

    Requires authentication to access.
    """
    permission_classes = [IsAuthenticated]

    PosteCreateSerializer = DirectsSerializer

    def get(self, request):
        """
        Handle HTTP GET request to retrieve a list of received and sent direct messages for the authenticated user.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            Response: The HTTP response containing the list of received and sent direct messages.

        """

        received_messages = Directs.objects.filter(to_user=request.user)
        sent_messages = Directs.objects.filter(from_user=request.user)

        serialized_received_messages = DirectsSerializer(
            received_messages, many=True)
        serialized_sent_messages = DirectsSerializer(sent_messages, many=True)

        data = {
            'received_messages': serialized_received_messages.data,
            'sent_messages': serialized_sent_messages.data,
        }

        return Response({'directs': data}, status=status.HTTP_200_OK)


class DirectView(APIView):
    """
    API endpoint for retrieving a specific direct message.

    Requires authentication to access.
    """

    PosteCreateSerializer = DirectsSerializer

    def get(self, request, direct_id):
        """
        Handle HTTP GET request to retrieve a specific direct message.

        Args:
            request (HttpRequest): The HTTP request object.
            direct_id (int): The ID of the direct message to retrieve.

        Returns:
            Response: The HTTP response containing the requested direct message.

        Raises:
            Http404: If the direct message with the given ID does not exist.
        """

        direct = get_object_or_404(Directs, id=direct_id)

        if request.user.id != direct.to_user.id and request.user.id != direct.from_user.id:
            return Response({'message': 'You do not have the necessary access to this message.'},
                            status=status.HTTP_403_FORBIDDEN)
        else:
            serialized_direct = DirectsSerializer(direct)
            return Response({"direct": serialized_direct.data}, status=status.HTTP_200_OK)


class SendDirectView(APIView):
    """
    API endpoint for sending a direct message to a user.

    Requires authentication to access.
    """
    PosteCreateSerializer = DirectsCreateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, username):
        """
        Handle HTTP POST request to send a direct message to a user.

        Args:
            request (HttpRequest): The HTTP request object.
            username (str): The username of the recipient user.

        Returns:
            Response: The HTTP response containing the result of the operation.

        Raises:
            Http404: If the sender or recipient user does not exist.
        """
        serializer = DirectsCreateSerializer(data=request.data)

        if serializer.is_valid():
            # Save the direct message object to the database
            serializer.save(
                from_user=get_object_or_404(User, id=request.user.id),
                to_user=get_object_or_404(User, username=username),
            )
            return Response({'message': 'Direct message sent successfully.'}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
