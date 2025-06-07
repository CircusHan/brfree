import os
import google.generativeai as genai
from flask import Blueprint, request, jsonify, render_template
import base64
from io import BytesIO
# PIL might be needed for image validation or manipulation, but not directly for API call if blobs are correct
# from PIL import Image

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api') # Added url_prefix for /api

# System Prompt / Instructions for the Gemini Model (Synthesized from Kiosk2 context)
# This prompt guides the chatbot's behavior, personality, and response format.
SYSTEM_INSTRUCTION_PROMPT = """당신은 대한민국 공공 보건소의 친절하고 유능한 AI 안내원 '늘봄이'입니다. 당신의 주요 임무는 보건소 방문객들에게 필요한 정보와 지원을 제공하는 것입니다.

**당신의 역할:**
- 보건소의 다양한 서비스, 부서, 진료 절차, 건강 프로그램 등에 대한 정보를 제공합니다.
- 방문객의 질문에 명확하고 간결하며 이해하기 쉽게 답변합니다.
- 항상 친절하고 공손한 태도를 유지하며, 방문객이 편안함을 느낄 수 있도록 돕습니다.
- 복잡하거나 민감한 문의에 대해서는 적절한 보건소 직원에게 안내하거나, 추가 정보를 찾아볼 수 있는 방법을 제시합니다.
- 응급 상황 시 대처 요령을 안내하고, 필요시 즉시 도움을 요청할 수 있도록 안내합니다. (예: "즉시 119에 전화하시거나 가장 가까운 직원에게 알려주세요.")
- 개인적인 의학적 진단이나 처방은 제공하지 않으며, "의사 또는 전문 의료인과 상담하시는 것이 가장 좋습니다."와 같이 안내합니다.
- 당신의 답변은 한국어로 제공되어야 합니다.

**응답 스타일:**
- 긍정적이고 따뜻한 어조를 사용합니다.
- 가능한 한 전문 용어 사용을 피하고, 쉬운 단어로 설명합니다.
- 필요한 경우, 정보를 단계별로 안내하여 방문객이 쉽게 따라올 수 있도록 합니다.
- 이모티콘이나 과도한 감탄사 사용은 자제하고, 전문성을 유지합니다.

**제한 사항:**
- 보건소 업무와 관련 없는 농담이나 사적인 대화는 지양합니다.
- 개인정보를 묻거나 저장하지 않습니다.
- 정치적, 종교적 또는 논란의 여지가 있는 주제에 대해서는 중립적인 입장을 취하거나 답변을 정중히 거절합니다. ("죄송하지만, 해당 질문에 대해서는 답변드리기 어렵습니다.")

**이미지 입력 처리 (해당되는 경우):**
- 사용자가 이미지를 제공하면, 이미지의 내용을 이해하고 관련된 질문에 답변할 수 있습니다. (예: "이것은 무슨 약인가요?" 또는 "이 증상에 대해 알려주세요.")
- 이미지에 있는 글자를 읽고 해석할 수 있습니다.
- 이미지에 대한 분석이 불가능하거나 부적절한 경우, 정중하게 추가 정보를 요청하거나 답변할 수 없음을 알립니다.

이제 방문객의 질문에 답변해주세요."""

@chatbot_bp.route('/chatbot', methods=['POST'])
def handle_chatbot_request():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": "API key not configured"}), 500

    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        # This could catch issues with the API key format or other genai config errors
        return jsonify({"error": f"Failed to configure Generative AI: {str(e)}"}), 500

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON request"}), 400

    user_question = data.get('message')
    base64_image_data = data.get('base64_image_data') # Optional

    if not user_question:
        return jsonify({"error": "No message (user_question) provided"}), 400

    model_name = "gemini-1.5-flash-latest" # Or whichever model Kiosk2 used / is preferred
    model = genai.GenerativeModel(model_name)

    prompt_parts = [SYSTEM_INSTRUCTION_PROMPT, "\n\n사용자 질문:\n"]

    if base64_image_data:
        try:
            # Remove potential data URI prefix (e.g., "data:image/jpeg;base64,")
            if ',' in base64_image_data:
                header, base64_image_data = base64_image_data.split(',', 1)
                # Infer mime_type from header if possible, otherwise default or require it
                mime_type = header.split(';')[0].split(':')[1] if header.startswith('data:') else "image/jpeg"
            else:
                # Assume it's raw base64 data, default mime_type
                mime_type = "image/jpeg" # Or require client to send mime_type

            image_bytes = base64.b64decode(base64_image_data)

            # Optional: Validate image using Pillow (robustness)
            # try:
            #     img = Image.open(BytesIO(image_bytes))
            #     img.verify() # Verify it's a valid image
            #     mime_type = Image.MIME.get(img.format) # Get accurate mime_type
            # except Exception as img_e:
            #     return jsonify({"error": f"Invalid image data: {str(img_e)}"}), 400

            image_blob = {"mime_type": mime_type, "data": image_bytes}
            prompt_parts.insert(1, image_blob) # Insert image before the user question but after system prompt
        except Exception as e:
            return jsonify({"error": f"Error processing image data: {str(e)}"}), 400

    prompt_parts.append(user_question)

    try:
        # Generation config can be added here if needed (temperature, top_k, etc.)
        # generation_config = genai.types.GenerationConfig(temperature=0.7)
        response = model.generate_content(prompt_parts) #, generation_config=generation_config)

        # Check for safety ratings and blockages as in Kiosk2
        if not response.candidates:
            # This case might occur if the prompt itself was blocked even before generation attempt,
            # or if no candidates were generated for other reasons.
            # Check response.prompt_feedback if available and has block reason
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                block_reason = response.prompt_feedback.block_reason.name
                error_message = f"요청이 안전 설정에 의해 차단되었습니다. 이유: {block_reason}. 다른 질문을 시도해주세요."
                return jsonify({"error": "Blocked by safety settings", "details": error_message, "reply": error_message}), 400
            return jsonify({"error": "No response generated", "reply": "죄송합니다. 현재 답변을 생성할 수 없습니다. 잠시 후 다시 시도해주세요."}), 500


        # Accessing .text directly is common, but Kiosk2 checks candidates
        # Ensure there's at least one candidate and it has content
        if not response.candidates[0].content.parts:
             # Check if the candidate was blocked
            finish_reason = response.candidates[0].finish_reason
            if finish_reason == genai.types.Candidate.FinishReason.SAFETY:
                safety_ratings_info = str(response.candidates[0].safety_ratings)
                error_message = f"답변이 안전 설정에 의해 차단되었습니다. ({safety_ratings_info}). 다른 질문을 시도해주세요."
                return jsonify({"error": "Response blocked by safety settings", "reply": error_message}), 400
            elif finish_reason != genai.types.Candidate.FinishReason.STOP:
                error_message = f"답변 생성 중 예상치 못한 이유로 중단되었습니다: {finish_reason.name}. 다른 질문을 시도해주세요."
                return jsonify({"error": "Response generation stopped", "reply": error_message}), 500

            # If no safety block but also no parts (empty response)
            return jsonify({"reply": "죄송합니다. 질문에 대한 답변을 찾지 못했습니다."})


        bot_response_text = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, "text"))
        if not bot_response_text.strip():
             # This handles cases where the response might be empty or only whitespace
            bot_response_text = "죄송합니다. 현재 적절한 답변을 드리기 어렵습니다. 다른 방식으로 질문해주시겠어요?"


        return jsonify({"reply": bot_response_text})

    except genai.types.BlockedPromptException as bpe:
        # This exception is specifically for when the prompt is blocked.
        # The general check above for response.prompt_feedback might catch this too.
        block_reason = str(bpe) # The exception itself might contain the reason
        error_message = f"요청이 안전 설정에 의해 차단되었습니다: {block_reason}. 다른 질문을 시도해주세요."
        return jsonify({"error": "Blocked by safety settings", "details": error_message, "reply": error_message}), 400
    except Exception as e:
        # General error handling for API calls or other unexpected issues
        # Log the error for server-side review: print(f"Error generating content: {e}")
        return jsonify({"error": f"Error generating content: {str(e)}", "reply": "죄송합니다. AI 서비스와 통신 중 오류가 발생했습니다."}), 500

# Example of how to register this blueprint in app/__init__.py:
# from .routes.chatbot import chatbot_bp
# app.register_blueprint(chatbot_bp)

@chatbot_bp.route('/interface')
def chatbot_interface():
    """Renders the chatbot interface page."""
    return render_template("chatbot_interface.html")
