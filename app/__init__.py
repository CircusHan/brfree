# app/__init__.py
from flask import Flask

def create_app() -> Flask:
    """
    애플리케이션 팩토리
    """
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )

    # (선택) 세션 암호키 – 실제 서비스에서는 환경 변수로 관리 권장
    app.secret_key = "replace-with-your-secret"

    # ── Blueprint를 지연(Lazy) Import 후 등록 ───────────────────
    #   * 순환 참조를 피하기 위해 함수 내부에서 import
    #   * 각 Blueprint 파일은 'app.routes.<module>' 아래에 존재
    from app.routes.home       import home_bp
    from app.routes.reception  import reception_bp
    from app.routes.certificate import certificate_bp
    from app.routes.payment    import payment_bp
    from app.routes.chatbot    import chatbot_bp # Added chatbot blueprint import

    app.register_blueprint(home_bp)        # "/"
    app.register_blueprint(reception_bp)   # "/reception"
    app.register_blueprint(certificate_bp) # "/certificate"
    app.register_blueprint(payment_bp)     # "/payment"
    app.register_blueprint(chatbot_bp)     # "/api/chatbot" (as per url_prefix in chatbot.py)

    return app
