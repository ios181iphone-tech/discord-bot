class DataManager:

    def __init__(self):
        self.data_file = Config.DATA_FILE
        self.backup_file = Config.BACKUP_FILE
        self.data = self.load()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.voice_sessions: Dict[str, Dict[str, Any]] = {}
        logger.info("Data Manager initialized")

    def load(self) -> Dict:
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        logger.warning("Data file is empty, creating new data")
                        return self.get_default_data()

                    data = json.loads(content)

                    if "users" not in data:
                        data["users"] = {}
                    if "last_reset" not in data:
                        data["last_reset"] = str(datetime.now())
                    if "total_logins" not in data:
                        data["total_logins"] = 0
                    if "total_logouts" not in data:
                        data["total_logouts"] = 0
                    if "stats" not in data:
                        data["stats"] = {"black_total": 0, "superme_total": 0}

                    logger.info(f"Data loaded from {self.data_file}")
                    return data
            else:
                logger.info("Data file not found, creating new data")
                return self.get_default_data()

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            if os.path.exists(self.backup_file):
                try:
                    with open(self.backup_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        logger.info("Recovered data from backup")
                        return data
                except:
                    pass
            return self.get_default_data()

        except Exception as e:
            logger.error(f"Error loading data: {e}")
            traceback.print_exc()
            return self.get_default_data()

    def get_default_data(self) -> Dict:
        return {
            "users": {},
            "last_reset": str(datetime.now()),
            "total_logins": 0,
            "total_logouts": 0,
            "stats": {
                "black_total": 0,
                "superme_total": 0
            }
        }

    def save(self):
        try:
            if os.path.exists(self.data_file):
                shutil.copy2(self.data_file, self.backup_file)

            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)

            logger.debug("Data saved successfully")

        except Exception as e:
            logger.error(f"Error saving data: {e}")
            traceback.print_exc()

    def add_time(self, user_id: str, seconds: int, admin_type: str):
        if "users" not in self.data:
            self.data["users"] = {}

        current = self.data["users"].get(user_id, 0)
        self.data["users"][user_id] = current + seconds

        if "stats" not in self.data:
            self.data["stats"] = {"black_total": 0, "superme_total": 0}

        if admin_type == "black":
            self.data["stats"]["black_total"] = self.data["stats"].get("black_total", 0) + seconds
        else:
            self.data["stats"]["superme_total"] = self.data["stats"].get("superme_total", 0) + seconds

        self.save()
        logger.info(f"Added {seconds} seconds to user {user_id}")

    def get_user_time(self, user_id: str) -> int:
        if "users" not in self.data:
            return 0
        return self.data["users"].get(user_id, 0)

    def reset_all(self):
        before_count = len(self.data.get("users", {}))
        before_total = sum(self.data.get("users", {}).values()) / 3600

        self.data["users"] = {}
        self.data["last_reset"] = str(datetime.now())
        self.data["stats"] = {"black_total": 0, "superme_total": 0}
        self.save()

        logger.info(f"Reset all data - {before_count} users, {before_total:.1f} hours total")
        return before_count, before_total
