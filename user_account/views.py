from django.shortcuts import redirect, get_object_or_404
from django.contrib.sites.shortcuts import get_current_site
from rest_framework import generics
from rest_framework.views import APIView
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import authenticate, login
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from django.http import HttpResponse
from django.urls import reverse
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from .models import CustomUser
from rest_framework import status
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .serializers import RegisterSerializer, LoginSerializer

class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Generate activation token and UID
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Get the current domain
            current_site = get_current_site(request)
            domain = current_site.domain

            # Create activation link
            activation_link = reverse('activate', kwargs={'uidb64': uid, 'token': token})
            activation_url = f'http://{domain}{activation_link}'

            # Email subject and message
            subject = 'Activate Your Account'

            # Plain text message
            text_message = f'Hi {user.username},\nPlease use the link below to activate your account:\n{activation_url}'

            # HTML message
            html_message = render_to_string('registration/activation_email.html', {
                'user': user,
                'activation_url': activation_url
            })

            # Send the email using EmailMultiAlternatives
            email = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, [user.email])
            email.attach_alternative(html_message, "text/html")
            email.send()

            return Response({'message': 'Registration successful. Please check your email to activate your account.'}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect('https://srr23.github.io/Recipe_Website_FrontEnd/login.html')  # Redirect to login page after activation
    else:
        return HttpResponse('Activation link is invalid!')


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            user = authenticate(username=username, password=password)
            
            if user:
                # Create or retrieve token for the user
                token, _ = Token.objects.get_or_create(user=user)

                # Log in the user
                login(request, user)

                # Return token and username in the response
                return Response({'token': token.key, 'username': user.username}, status=status.HTTP_200_OK)
            else:
                # Invalid credentials error
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # If serializer is not valid, return validation errors with a 400 Bad Request status
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class LoginView(APIView):
#     def post(self, request):
#         serializer = LoginSerializer(data = self.request.data)
#         if serializer.is_valid():
#             username = serializer.validated_data['username']
#             password = serializer.validated_data['password']

#             user = authenticate(username= username, password=password)
            
#             if user:
#                 token, _ = Token.objects.get_or_create(user=user)
#                 # print(token)
#                 # print(_)
#                 login(request, user)
#                 return Response({'token' : token.key, 'username' : user.username})
#             else:
#                 return Response({'error' : "Invalid Credential"})
#         return Response(serializer.errors)


@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Get the user's token
            token = Token.objects.get(user=request.user)
            # Delete the token
            token.delete()
            return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
        except Token.DoesNotExist:
            return Response({"error": "Invalid operation, token not found."}, status=status.HTTP_400_BAD_REQUEST)

