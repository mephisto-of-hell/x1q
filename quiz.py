# quiz.py
from telethon.tl.types import InputMediaPoll, Poll, PollAnswer
from database import get_group_settings, get_random_question, insert_active_poll, get_question_by_poll_id, update_user_score

async def post_quiz_poll(client, group_id):
    """Post a quiz poll to a group."""
    settings = get_group_settings(group_id)
    language = settings["language"] if settings else "en"
    question = get_random_question(language)
    if not question:
        await client.send_message(group_id, f"No questions available in {language}!")
        return
    question_text = question["question_text"]
    options = question["options"]
    correct_option = question["correct_option"] - 1  # Convert to 0-based for Telegram
    poll = InputMediaPoll(
        poll=Poll(
            question=question_text,
            answers=[PollAnswer(opt, bytes([i])) for i, opt in enumerate(options)],
            quiz=True,
            correct_option_id=correct_option
        )
    )
    message = await client.send_message(group_id, file=poll)
    poll_id = message.poll.poll.id
    insert_active_poll(poll_id, group_id, question["id"])

async def handle_poll_answer(client, event):
    """Handle a user's poll answer."""
    poll_id = event.poll_id
    user_id = event.user_id
    selected_option = event.option_ids[0]
    result = get_question_by_poll_id(poll_id)
    if not result:
        return
    question = result["question"]
    group_id = result["group_id"]
    correct_option = question["correct_option"] - 1  # 0-based
    if selected_option == correct_option:
        update_user_score(group_id, user_id, 1)