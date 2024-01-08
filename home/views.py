from proof.models import Poste
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from home.serializers import PosteSerializer, UserSerializer
from proof.models import Relation
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated

User = get_user_model()


class ExploreView(APIView):
    """
    API view for retrieving posts and users.

    This view retrieves all posts and users from the database. It also provides
    filtering functionality based on a search term.

    - To retrieve all posts and users, make a GET request to the endpoint.
    - To filter posts and users based on a search term, include the 'search'
      query parameter in the request.

    Note: The search term is case-sensitive.
    Responses:
    - 200: Successful response with a list of posts and users.
    """

    def get(self, request):
        """
        Get posts and users.

        Retrieves all posts and users from the database. Optionally filters
        posts and users based on a search term.

        Query Parameters:
        - search (optional): Search term for filtering posts and users.

        Returns:
        - 200: Successful response with a list of posts and users.
        """
        # Retrieve all posts and users from the database
        posts = Poste.objects.all()
        users = User.objects.all()

        if request.GET.get("search"):
            posts = posts.filter(body__contains=request.GET.get("search"))
            users = users.filter(username__contains=request.GET.get("search"))

        post_serializer = PosteSerializer(posts, many=True)
        user_serializer = UserSerializer(users, many=True)

        return Response({
            'posts': post_serializer.data,
            'users': user_serializer.data,
        })


class HomeView(APIView):
    """
    API view for exploring posts and users.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Handle GET request for exploring posts and users.
        """

        temp = Relation.objects.filter(from_user=request.user).values("to_user")

        posts = Poste.objects.filter(user__in=temp)

        users = Relation.objects.filter(from_user=request.user).values("to_user")

        if request.GET.get("search"):
            posts = posts.filter(body__contains=request.GET.get("search"))
            users = users.filter(username__contains=request.GET.get("search"))

        post_serializer = PosteSerializer(posts, many=True)
        user_serializer = UserSerializer(users, many=True)

        return Response({
            'posts': post_serializer.data,
            'users': user_serializer.data,
        })
