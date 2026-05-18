from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def slack_config():
    # SLACK_BOT_TOKEN = os.getenv("SLACK")
    client = WebClient(token="xoxb-2192053652768-11085603296470-bL1s3vwzrcXZChZUxlhyASGH")
    return client


client = slack_config()

def get_user_id_by_email(email: str):
    try:
        response = client.users_lookupByEmail(email=email)
        return response["user"]["id"]

    except SlackApiError as e:
        print(f"Slack Error: {e.response['error']}")
        return None


def send_dm_by_email(email: str, message: str):
    try:
        user_id = get_user_id_by_email(email)

        if not user_id:
            print("User not found")
            return False

        response = client.chat_postMessage(
            channel=user_id,
            text=message
        )

        return response

    except SlackApiError as e:
        print(f"Slack Error: {e.response['error']}")
        return False


def upload_file_to_slack(email: str, uploaded_file):
    """
    uploaded_file = request.FILES['file']
    """

    try:
        user_id = get_user_id_by_email(email)

        if not user_id:
            print("User not found")
            return False

        # Open DM conversation
        conversation = client.conversations_open(
            users=[user_id]
        )

        channel_id = conversation["channel"]["id"]

        # Upload file
        response = client.files_upload_v2(
            channel=channel_id,
            file=uploaded_file.read(),
            filename=uploaded_file.name,
            title=uploaded_file.name,
        )

        return response

    except SlackApiError as e:
        print(f"Slack Upload Error: {e.response['error']}")
        return False

if __name__ == '__main__':
    pass
