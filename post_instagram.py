import os
import requests
from dotenv import load_dotenv
from datetime import datetime

# 환경 변수 로드
load_dotenv()

class InstagramAPI:
    def __init__(self):
        """Initialize Instagram API with credentials from environment variables"""
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
        
        if not self.access_token or not self.account_id:
            raise ValueError("Instagram 자격 증명이 설정되지 않았습니다. .env 파일을 확인해주세요.")
        
        self.api_version = "v18.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    def _create_single_media(self, image_url, caption=""):
        """
        단일 이미지 미디어 컨테이너 생성
        
        Args:
            image_url (str): 이미지 URL
            caption (str): 이미지 설명
            
        Returns:
            dict: API 응답 데이터
        """
        container_url = f"{self.base_url}/{self.account_id}/media"
        container_params = {
            "access_token": self.access_token,
            "image_url": image_url,
            "caption": caption
        }
        
        response = requests.post(container_url, params=container_params)
        response.raise_for_status()
        return response.json()

    def _create_carousel_item(self, image_url):
        """
        캐러셀 아이템 생성
        
        Args:
            image_url (str): 이미지 URL
            
        Returns:
            dict: API 응답 데이터
        """
        container_url = f"{self.base_url}/{self.account_id}/media"
        container_params = {
            "access_token": self.access_token,
            "image_url": image_url,
            "is_carousel_item": True
        }
        
        response = requests.post(container_url, params=container_params)
        response.raise_for_status()
        return response.json()

    def _create_carousel_container(self, children_ids, caption=""):
        """
        캐러셀 컨테이너 생성
        
        Args:
            children_ids (list): 캐러셀 아이템 ID 리스트
            caption (str): 캐러셀 설명
            
        Returns:
            dict: API 응답 데이터
        """
        container_url = f"{self.base_url}/{self.account_id}/media"
        container_params = {
            "access_token": self.access_token,
            "media_type": "CAROUSEL",
            "children": ",".join(children_ids),
            "caption": caption
        }
        
        response = requests.post(container_url, params=container_params)
        response.raise_for_status()
        return response.json()

    def _publish_media(self, creation_id):
        """
        미디어 게시
        
        Args:
            creation_id (str): 생성된 미디어 ID
            
        Returns:
            dict: API 응답 데이터
        """
        publish_url = f"{self.base_url}/{self.account_id}/media_publish"
        publish_params = {
            "access_token": self.access_token,
            "creation_id": creation_id
        }
        
        response = requests.post(publish_url, params=publish_params)
        response.raise_for_status()
        return response.json()

    def _get_formatted_date(self):
        """현재 날짜를 포맷팅된 문자열로 반환"""
        weekdays = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
        now = datetime.now()
        weekday = weekdays[now.weekday()]
        return f"{now.year}년 {now.month:02d}월 {now.day:02d}일 {weekday} MQ 글로벌 증권가 뉴스"

    def post_image(self, image_paths, caption=None):
        """
        Instagram에 이미지를 포스팅합니다.
        
        Args:
            image_paths (str or list): 업로드할 이미지 URL 또는 URL 리스트
            caption (str, optional): 포스트에 포함될 캡션 텍스트. None이면 자동 생성됨.
            
        Returns:
            dict: 성공 시 {"success": True, "post_id": "..."}, 실패 시 {"success": False, "error": "에러 메시지"}
        """
        try:
            # 캡션이 None이면 현재 날짜로 생성
            if caption is None:
                caption = self._get_formatted_date()
            
            # 단일 이미지인 경우 리스트로 변환
            if isinstance(image_paths, str):
                image_paths = [image_paths]

            # 이미지가 여러 장인 경우 캐러슬로 처리
            if len(image_paths) > 1:
                print(f"캐러셀 이미지 업로드 중... (총 {len(image_paths)}장)")
                
                # 각 이미지를 캐러셀 아이템으로 생성
                children_ids = []
                for i, image_url in enumerate(image_paths, 1):
                    print(f"이미지 {i}/{len(image_paths)} 처리 중...")
                    response = self._create_carousel_item(image_url)
                    if "id" not in response:
                        return {"success": False, "error": f"캐러셀 아이템 {i} 생성 실패"}
                    children_ids.append(response["id"])
                
                # 캐러셀 컨테이너 생성
                print("캐러셀 컨테이너 생성 중...")
                container = self._create_carousel_container(children_ids, caption)
                
            else:  # 단일 이미지 처리
                print("단일 이미지 업로드 중...")
                container = self._create_single_media(image_paths[0], caption)

            if "id" not in container:
                return {"success": False, "error": "미디어 컨테이너 ID를 받지 못했습니다"}
            
            # 미디어 게시
            print("Instagram에 게시물 발행 중...")
            publish_data = self._publish_media(container["id"])
            
            if "id" not in publish_data:
                return {"success": False, "error": "게시물 ID를 받지 못했습니다"}
            
            print("게시물 발행 완료!")
            return {
                "success": True, 
                "post_id": publish_data["id"],
                "status": "이미지가 성공적으로 Instagram에 업로드되었습니다. 원본 파일은 이제 삭제해도 됩니다."
            }
            
        except requests.exceptions.RequestException as e:
            error_message = str(e)
            if hasattr(e.response, 'json'):
                try:
                    error_data = e.response.json()
                    if 'error' in error_data:
                        error_message = f"{error_data['error'].get('message', str(e))}"
                except ValueError:
                    pass
            return {"success": False, "error": f"Instagram 포스팅 중 오류 발생: {error_message}"}


if __name__ == "__main__":
    api = InstagramAPI()
    
    # 테스트 이미지 URL
    single_image = "https://petapixel.com/assets/uploads/2022/06/what-is-a-jpeg-featured-800x420.jpg"
    multiple_images = [
        "https://petapixel.com/assets/uploads/2022/06/what-is-a-jpeg-featured-800x420.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png"
    ]
    
    # 단일 이미지 테스트
    print("\n=== 단일 이미지 테스트 ===")
    result = api.post_image(single_image)
    if result["success"]:
        print(f"포스팅 성공! 게시물 ID: {result['post_id']}")
        print(result["status"])
    else:
        print(f"포스팅 실패: {result['error']}")
    
    # 다중 이미지 테스트
    print("\n=== 다중 이미지 테스트 ===")
    result = api.post_image(multiple_images)
    if result["success"]:
        print(f"포스팅 성공! 게시물 ID: {result['post_id']}")
        print(result["status"])
    else:
        print(f"포스팅 실패: {result['error']}")
