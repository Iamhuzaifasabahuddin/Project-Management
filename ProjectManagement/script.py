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
        return response['user']['id']
    except SlackApiError as e:
        print(e)
        # logging.error(f"Error finding user: {e.response['error']}")
        return None


def send_dm(user_id: str, message: str):
    try:
        client.chat_postMessage(channel=user_id, text=message)
    except SlackApiError as e:
        print(e)
        # logging.error(f"Error sending DM: {e.response['error']}")
        return None


if __name__ == '__main__':
    send_dm(get_user_id_by_email("huzaifa.sabah@topsoftdigitals.pk"), "Hello from the script!")