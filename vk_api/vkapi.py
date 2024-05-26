import socket
import ssl
import json
import argparse


# Метод для выполнения HTTPS-запросов
def https_request(host, path):
    context = ssl.create_default_context()

    with socket.create_connection((host, 443)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
            ssock.sendall(request.encode('utf-8'))

            response = b""
            while True:
                data = ssock.recv(4096)
                if not data:
                    break
                response += data

    headers, body = response.split(b"\r\n\r\n", 1)
    return body.decode('utf-8')


# Метод для выполнения запросов к API ВКонтакте
def vk_api_request(method, params):
    host = "api.vk.com"
    path = f"/method/{method}?" + "&".join([f"{k}={v}" for k, v in params.items()])
    try:
        response = https_request(host, path)
        return json.loads(response)
    except socket.timeout:
        print("Ошибка: Превышено время ожидания запроса.")
    except socket.error as e:
        print(f"Ошибка сокета: {e}")
    except ssl.SSLError as e:
        print(f"Ошибка SSL: {e}")
    except json.JSONDecodeError:
        print("Ошибка: Не удалось разобрать ответ.")
    return None


# Метод для получения числового ID пользователя по его screen name
def resolve_screen_name(screen_name, access_token):
    params = {
        "user_ids": screen_name,
        "access_token": access_token,
        "v": "5.131"
    }
    response = vk_api_request("users.get", params)
    if response and 'response' in response and len(response['response']) > 0:
        return response['response'][0]['id']
    elif response and 'error' in response:
        print(f"Ошибка {response['error']['error_code']}: {response['error']['error_msg']}")
    return None


# Метод для получения списка друзей пользователя
def get_friends(user_id, access_token):
    params = {
        "user_id": user_id,
        "access_token": access_token,
        "v": "5.131"
    }
    response = vk_api_request("friends.get", params)
    if response and 'response' in response:
        return response['response']['items']
    elif response and 'error' in response:
        print(f"Ошибка {response['error']['error_code']}: {response['error']['error_msg']}")
    return []


# Метод для получения информации о друзьях пользователя
def get_friend_info(friend_ids, access_token):
    friends_info = []
    for friend_id in friend_ids:
        params = {
            "user_ids": friend_id,
            "fields": "first_name,last_name",
            "access_token": access_token,
            "v": "5.131"
        }
        response = vk_api_request("users.get", params)
        if response and 'response' in response:
            friends_info.extend(response['response'])
        elif response and 'error' in response:
            print(f"Ошибка {response['error']['error_code']}: {response['error']['error_msg']}")
    return friends_info


# Метод для печати списка друзей
def print_friends(friends):
    print("Список друзей:")
    for friend in friends:
        print(f"{friend['first_name']} {friend['last_name']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Получить список друзей пользователя ВКонтакте.")
    parser.add_argument("user_id", type=str, help="ID или screen name пользователя ВКонтакте")
    parser.add_argument("command", type=str, choices=["friends"], help="Команда для выполнения")

    args = parser.parse_args()
    user_id = args.user_id
    command = args.command

    # Чтение access_token из файла token.txt
    try:
        with open("token.txt", "r") as file:
            access_token = file.read().strip()
    except FileNotFoundError:
        print("Ошибка: Файл token.txt не найден.")
        exit(1)
    except Exception as e:
        print(f"Ошибка при чтении файла token.txt: {e}")
        exit(1)

    if not user_id.isdigit():
        resolved_id = resolve_screen_name(user_id, access_token)
        if resolved_id:
            user_id = resolved_id
        else:
            print("Не удалось разрешить screen name пользователя.")
            exit(1)

    if command == "friends":
        friends_ids = get_friends(user_id, access_token)

        if friends_ids:
            friends_info = get_friend_info(friends_ids, access_token)

            print_friends(friends_info)
        else:
            print("Не удалось получить список друзей.")
