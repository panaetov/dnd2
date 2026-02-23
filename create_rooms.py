import json
import time
import uuid

import requests

JANUS_URL = "http://51.250.102.96:8088/janus"
# Если у вас включен API Secret, добавьте заголовок 'X-Admin-Key' или параметр apisecret


def create_rooms(count=100, start_room_id=1001):
    session_id = None
    handle_id = None

    try:
        # 1. Создаем сессию
        resp = requests.post(
            JANUS_URL,
            json={
                "janus": "create",
                "transaction": str(uuid.uuid4()),
            },
        ).json()
        if resp["janus"] != "success":
            raise Exception("Failed to create session")
        session_id = resp["data"]["id"]
        print(f"Session created: {session_id}")

        # 2. Прикрепляемся к плагину VideoRoom
        attach_req = {
            "janus": "attach",
            "plugin": "janus.plugin.videoroom",
            "transaction": str(uuid.uuid4()),
        }
        resp = requests.post(f"{JANUS_URL}/{session_id}", json=attach_req).json()
        if resp["janus"] != "success":
            raise Exception("Failed to attach plugin")
        handle_id = resp["data"]["id"]
        print(f"Handle created: {handle_id}")

        # 3. Создаем комнаты в цикле
        for i in range(count):
            room_id = start_room_id + i
            transaction = f"tx_create_{room_id}"

            body = {
                "request": "create",
                "room": room_id,
                "permanent": True,  # Важно: сохраняет в конфиг файл
                "description": f"Pre-generated Room {i+1}",
                "publishers": 10,  # Макс кол-во издателей
                "bitrate": 512000,  # Битрейт по умолчанию
                "fir_freq": 10,
                # "audiocodec": "opus",
                # "videocodec": "vp8"
            }

            req = {"janus": "message", "body": body, "transaction": transaction}

            resp = requests.post(
                f"{JANUS_URL}/{session_id}/{handle_id}", json=req
            ).json()

            if resp.get("janus") == "success" or resp.get("videoroom") == "created":
                print(f"Room {room_id} created successfully.")
            else:
                # Если комната уже существует, Janus вернет ошибку или существующий статус
                print(
                    f"Room {room_id} status: {resp.get('error_code', 'N/A')} - {resp.get('error', 'N/A')}"
                )

            # Небольшая задержка, чтобы не спамить API слишком быстро
            time.sleep(0.05)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # 4. Очищаем за собой (опционально, комнаты останутся из-за permanent: true)
        if session_id:
            requests.delete(f"{JANUS_URL}/{session_id}")
            print("Session destroyed.")


if __name__ == "__main__":
    create_rooms(count=100, start_room_id=1000)
