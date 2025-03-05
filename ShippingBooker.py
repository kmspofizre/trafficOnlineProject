from requests import Session, Response
from constants import headers_post, post_application_query
from logging import Logger


class ShippingBooker:
    def __init__(self, session: Session, api_key: str):
        self.post_header = headers_post
        headers_post['Authorization'] = f"Bearer {api_key}"
        self.session = session
        super().__init__()

    def book_shipping(self, shipping_id: str) -> Response:
        booking_response = self.session.post(
            f"{post_application_query}{shipping_id}/reserve",
            headers=headers_post)
        return booking_response

    @staticmethod
    def process_booking_response(booking_response: Response, logger: Logger) -> bool:
        if booking_response.status_code == 200:
            logger.info("Gotcha!")
            logger.info(booking_response.json())
            return True
        else:
            logger.error(f"Couldn't book this shipping with error code: {booking_response.status_code}")
            logger.error(f"{booking_response.json()}")
            return False

    def update_headers(self, api_key: str):
        self.post_header['Authorization'] = f"Bearer {api_key}"

