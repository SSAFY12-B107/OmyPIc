# import httpx
# from fastapi import HTTPException, status

# from core.config import settings

# async def get_kakao_token(code: str) -> dict:
#     """카카오 액세스 토큰 요청"""
#     token_url = "https://kauth.kakao.com/oauth/token"
#     token_data = {
#         "grant_type": "authorization_code",
#         "client_id": settings.KAKAO_CLIENT_ID,
#         "client_secret": settings.KAKAO_CLIENT_SECRET,
#         "redirect_uri": settings.KAKAO_REDIRECT_URI,
#         "code": code,
#     }
    
#     async with httpx.AsyncClient() as client:
#         token_response = await client.post(token_url, data=token_data)
        
#         if token_response.status_code != 200:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Failed to get Kakao access token",
#             )
        
#         return token_response.json()

# async def get_kakao_user_info(access_token: str) -> dict:
#     """카카오 사용자 정보 요청"""
#     user_info_url = "https://kapi.kakao.com/v2/user/me"
#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
#     }
    
#     async with httpx.AsyncClient() as client:
#         user_response = await client.get(user_info_url, headers=headers)
        
#         if user_response.status_code != 200:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Failed to get Kakao user info",
#             )
        
#         user_info = user_response.json()
        
#         # 필수 정보 추출
#         kakao_account = user_info.get("kakao_account", {})
#         kakao_id = str(user_info.get("id"))
#         email = kakao_account.get("email")
#         nickname = kakao_account.get("profile", {}).get("nickname")
        
#         if not email or not nickname:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Required user information not provided by Kakao",
#             )
            
#         return {
#             "social_id": kakao_id,
#             "email": email,
#             "name": nickname,
#         }