enum Gender {
  FEMALE = 0,
  MALE = 1,
  OTHER = 2
}

struct Player {
  1: string id;
  2: string name;
  3: string created; // ISO 8601
  4: optional string modified; // ISO 8601
  5: optional Gender gender;
  6: optional string birthday; // ISO 8601
  7: optional string title = "beginner";
  8: string countryCode;
  9: optional string regionCode;
  10: optional string city;
  11: map<string,string> pictureUrls = {};
  12: optional string bio;
  13: optional set<string> performedActivities = [];
  14: optional set<string> followers = [];
  15: optional set<string> following = [];
  16: optional set<string> topicFollowing = [];
  17: optional set<string> blockers = [];
  18: optional set<string> blocking = [];
  19: optional set<string> rewards = [];
  20: optional set<string> permissions = [];
  21: optional set<string> featureFlags = [];
  22: optional bool active = true;
  23: optional bool teamMember = false;
  24: optional bool isPrivate = false;
  25: optional map<string,string> privacySettings = {};
  26: optional set<string> bannerSlugs = [];
  27: optional bool deactivated = false;
  28: optional bool deleted = false;
  29: optional string type = "player";
  31: optional map<string,string> powerUps = {};
  33: optional i32 consecutiveDays = 0;
  34: optional string consecutiveDaysUpdated; // ISO 8601
  35: optional string dailyRewardsUpdated; // ISO 8601
  36: optional string locale = "en";
}
