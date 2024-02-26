from json import load, dump, JSONDecodeError


class UserInfoManager:

    """
    Json file structure:
    "users": {
        "user_id": [
            {
                "role": "user", "content": "message"
            }, ...
        ], ...
    }
    """

    JSON_DATA_FILE_NAME = 'users_data.json'

    def __init__(self, user_id: str | int) -> None:

        self.user_id = str(user_id)

        # creates a file if it doesn't exist
        with open(self.JSON_DATA_FILE_NAME, 'a+') as _:
            pass

        with open(self.JSON_DATA_FILE_NAME, 'r') as f:

            self.default_user_data = []

            default_all_users_data = {'users': {self.user_id: self.default_user_data}}

            try:
                self.all_users_data = load(f) or default_all_users_data

            except JSONDecodeError:
                self.all_users_data = default_all_users_data

            self.current_user_data = self.all_users_data['users'].get(self.user_id, self.default_user_data)

    def __enter__(self):
        return self

    def __exit__(self, *_) -> None:
        self.save()

    def save(self) -> None:

        self.all_users_data['users'][self.user_id] = self.current_user_data

        with open(self.JSON_DATA_FILE_NAME, 'w+') as f:
            dump(self.all_users_data, f)

    def update_user_data(self, new_user_data: list[dict[str, str]]) -> None:
        self.current_user_data = new_user_data

    def get_user_data(self) -> list[dict[str, str]]:
        return self.current_user_data
