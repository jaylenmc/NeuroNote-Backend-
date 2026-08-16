from .serializers import PresignedUrlPost

def validate_data(request_data):
    data = PresignedUrlPost(data=request_data)
    data.is_valid(raise_exception=True)
    return data.validated_data