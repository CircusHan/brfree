# 간단한 하드코딩 번역 사전
TRANSLATIONS = {
    "ko": {
        "home_title":      "보건소에 오신 것을 환영합니다",
        "btn_checkin":     "① 접수(순번표)",
        "btn_payment":     "② 수납",
        "btn_certificate": "③ 증명서 발급",
    },
    "en": {
        "home_title":      "Welcome to the Public Health Center",
        "btn_checkin":     "① Reception (Queue Ticket)",
        "btn_payment":     "② Payment",
        "btn_certificate": "③ Issue Certificate",
    },
}

def get_locale(lang: str = "ko") -> dict:
    """
    요청한 언어 코드(ko|en)에 맞는 번역 dict 반환
    """
    return TRANSLATIONS.get(lang, TRANSLATIONS["ko"])
