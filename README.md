# MyKingdomBot

## English

### Introduction
MyKingdomBot is a sophisticated Telegram-based strategy game bot developed in Python using the `python-telegram-bot` library. It offers an immersive experience where players can establish and manage virtual kingdoms, acquire strategic equipment, form alliances, and engage in tactical operations against other players' kingdoms. The bot leverages SQLite for robust data persistence and includes a comprehensive admin panel for game management. With multilingual support (primarily Persian) and integration with Telegram channels, it provides a dynamic and interactive gaming environment.

### Key Features
- **Kingdom Establishment and Management**: Players can create and govern their own kingdoms, each with unique attributes and strategic importance.
- **Equipment System**: Purchase and deploy various equipment types, such as armies, spies, hackers, firewalls, and defensive shields, to enhance gameplay.
- **Alliance System**: Form strategic alliances with other kingdoms to share resources, prevent mutual attacks, and share victory rewards.
- **Attack and Defense Mechanics**: Execute operations like military attacks, espionage, and hacking, while defending your kingdom with strategic equipment.
- **Admin Panel**: Administrators have extensive controls to start/end games, set prices, manage users, and oversee game settings.
- **Telegram Channel Integration**: Supports mandatory channel subscriptions for player verification and broadcasts game updates via Telegram channels.
- **Persian Language Support**: Designed with Persian as the primary language, with potential for localization to other languages.
- **Database-Driven**: Utilizes SQLite to store game state, including user data, kingdom details, equipment inventories, and alliances.

### Requirements
- Python 3.8 or higher
- `python-telegram-bot` library (version 20.0 or higher)
- SQLite3 (included in Python standard library)
- `uuid` library (included in Python standard library)
- Standard Python libraries: `logging`, `asyncio`, `time`, `random`

### Installation
1. Install the required dependencies:
   ```bash
   pip install python-telegram-bot
   ```
2. Configure the Telegram bot token by replacing the `TOKEN` variable in the code with the token obtained from BotFather.
3. Ensure the SQLite database file (`war_game.db`) is created automatically upon running the script.
4. Run the bot:
   ```bash
   python bot.py
   ```

### Usage
- **Start the Game**: Initiate the bot by sending the `/start` command in Telegram.
- **Player Actions**: Use the interactive menu to establish a kingdom, purchase equipment, form alliances, or launch operations against other kingdoms.
- **Admin Functions**: Administrators can access the `/panel` command to manage game settings, including starting/ending games, setting prices, banning/unbanning users, and broadcasting messages.
- **Channel Verification**: Players must join mandatory Telegram channels for verification before participating in the game.
- **Gameplay Mechanics**: Players can engage in strategic operations (e.g., attacks, espionage) and must defend their kingdoms using equipment like firewalls and shields.

### Database Structure
The bot uses a SQLite database with the following tables:
- **users**: Stores player information (`user_id`, `username`, `is_banned`, `is_verified`).
- **countries**: Tracks kingdom details (`name`, `status`, `price`, `owner_id`), with statuses like available (✅), owned (❌), or destroyed (💀).
- **equipments**: Manages player equipment inventories (`user_id`, `country_name`, `equipment_id`, `quantity`).
- **game_settings**: Stores game configuration settings (`key`, `value`), such as game status and prize details.
- **admins**: Manages admin permissions (`user_id`, `permissions`) for fine-grained control over administrative actions.
- **required_channels**: Lists mandatory Telegram channels (`channel_username`) for player verification.
- **alliances**: Tracks alliances between kingdoms (`country1`, `country2`) to prevent attacks and enable resource sharing.

### Code Structure
- **Main Components**:
  - `Database` class: Handles SQLite database operations, including table creation, user management, and game state persistence.
  - `start` handler: Initiates the game, verifies channel subscriptions, and displays the main menu.
  - `panel` handler: Provides an admin interface for managing game settings and users.
  - `button` handler: Processes callback queries for interactive menu selections.
  - `message_handler`: Handles text input for actions like setting prices, sending messages, or processing payments.
- **Key Variables**:
  - `COUNTRIES`: Dictionary of available kingdoms with their initial status.
  - `EQUIPMENTS`: Dictionary of equipment types with names and prices (e.g., army, spy, firewall).
  - `ATTACK_EQUIPMENTS` and `DEFENSE_EQUIPMENTS`: Lists defining equipment roles.
  - `DAMAGE_VALUES`: Defines damage mechanics for attack operations.
  - `ADMIN_PERMISSIONS`: Lists available admin permissions for fine-grained control.
- **Asynchronous Design**: Uses `asyncio` for non-blocking Telegram API interactions, ensuring smooth performance.

### Contributing
Contributions are highly encouraged! To contribute:
1. Fork the repository on GitHub.
2. Make changes or add features to your fork.
3. Submit a pull request with a detailed description of your changes.
4. Report bugs or suggest improvements by opening issues on GitHub.

### License
This project is licensed under the MIT License.

---

## فارسی

### مقدمه
MyKingdomBot یک ربات بازی استراتژیک مبتنی بر تلگرام است که با استفاده از زبان پایتون و کتابخانه `python-telegram-bot` توسعه یافته است. این ربات تجربه‌ای جذاب و تعاملی ارائه می‌دهد که در آن بازیکنان می‌توانند ممالک مجازی خود را تأسیس و مدیریت کنند، تجهیزات استراتژیک خریداری کنند، اتحادهای استراتژیک تشکیل دهند و عملیات تاکتیکی علیه دیگر ممالک انجام دهند. این ربات از SQLite برای ذخیره‌سازی پایدار داده‌ها استفاده می‌کند و شامل یک پنل مدیریتی جامع برای مدیریت بازی است. با پشتیبانی از زبان فارسی و ادغام با کانال‌های تلگرام، محیطی پویا و کاربرپسند برای بازی فراهم می‌کند.

### ویژگی‌های کلیدی
- **تأسیس و مدیریت مملکت**: بازیکنان می‌توانند ممالک خود را با ویژگی‌ها و اهمیت استراتژیک منحصربه‌فرد تأسیس و مدیریت کنند.
- **سیستم تجهیزات**: خرید و استفاده از تجهیزات متنوع مانند ارتش، جاسوس، هکر، فایروال و سپر دفاعی برای بهبود گیم‌پلی.
- **سیستم اتحاد**: تشکیل اتحاد با دیگر ممالک برای اشتراک منابع، جلوگیری از حملات متقابل و تقسیم جوایز پیروزی.
- **مکانیزم حمله و دفاع**: اجرای عملیات‌هایی مانند حملات نظامی، جاسوسی و هک، و دفاع از مملکت با استفاده از تجهیزات استراتژیک.
- **پنل مدیریتی**: مدیران می‌توانند بازی را شروع یا پایان دهند، قیمت‌ها را تنظیم کنند، کاربران را مدیریت کنند و پیام‌های همگانی ارسال کنند.
- **ادغام با کانال‌های تلگرام**: پشتیبانی از عضویت اجباری در کانال‌ها برای تأیید بازیکنان و انتشار به‌روزرسانی‌های بازی از طریق کانال‌ها.
- **پشتیبانی از زبان فارسی**: ربات عمدتاً به زبان فارسی طراحی شده است و امکان بومی‌سازی برای زبان‌های دیگر را دارد.
- **پایگاه داده‌محور**: استفاده از SQLite برای ذخیره وضعیت بازی، اطلاعات کاربران، جزئیات ممالک و اتحادها.

### پیش‌نیازها
- پایتون نسخه 3.8 یا بالاتر
- کتابخانه `python-telegram-bot` (نسخه 20.0 یا بالاتر)
- SQLite3 (موجود در کتابخانه استاندارد پایتون)
- کتابخانه `uuid` (موجود در کتابخانه استاندارد پایتون)
- کتابخانه‌های استاندارد پایتون: `logging`، `asyncio`، `time`، `random`

### نصب
1. نصب وابستگی‌های مورد نیاز:
   ```bash
   pip install python-telegram-bot
   ```
2. تنظیم توکن ربات تلگرام با جایگزینی متغیر `TOKEN` در کد با توکن دریافت‌شده از BotFather.
3. فایل پایگاه داده SQLite (`war_game.db`) به‌صورت خودکار هنگام اجرای اسکریپت ایجاد می‌شود.
4. اجرای ربات:
   ```bash
   python bot.py
   ```

### نحوه استفاده
- **شروع بازی**: با ارسال دستور `/start` در تلگرام، بازی را آغاز کنید.
- **اقدامات بازیکنان**: از منوی تعاملی برای تأسیس مملکت، خرید تجهیزات، تشکیل اتحاد یا اجرای عملیات علیه دیگر ممالک استفاده کنید.
- **مدیریت ادمین**: مدیران می‌توانند با دستور `/panel` به پنل مدیریتی دسترسی پیدا کنند تا تنظیمات بازی، قیمت‌ها، کاربران و پیام‌های همگانی را مدیریت کنند.
- **تأیید عضویت در کانال**: بازیکنان باید در کانال‌های تلگرام اجباری عضو شوند تا مشارکت آنها تأیید شود.
- **مکانیزم‌های گیم‌پلی**: بازیکنان می‌توانند عملیات استراتژیک (مانند حملات، جاسوسی) انجام دهند و با استفاده از فایروال‌ها و سپرهای دفاعی از مملکت خود دفاع کنند.

### ساختار پایگاه داده
ربات از یک پایگاه داده SQLite با جداول زیر استفاده می‌کند:
- **users**: ذخیره اطلاعات بازیکنان (`user_id`، `username`، `is_banned`، `is_verified`).
- **countries**: ردیابی جزئیات ممالک (`name`، `status`، `price`، `owner_id`) با وضعیت‌هایی مانند موجود (✅)، متعلق به بازیکن (❌) یا سقوط‌کرده (💀).
- **equipments**: مدیریت موجودی تجهیزات بازیکنان (`user_id`، `country_name`، `equipment_id`، `quantity`).
- **game_settings**: ذخیره تنظیمات بازی (`key`، `value`) مانند وضعیت بازی و جزئیات جایزه.
- **admins**: مدیریت دسترسی‌های مدیران (`user_id`، `permissions`) برای کنترل دقیق اقدامات مدیریتی.
- **required_channels**: لیست کانال‌های تلگرام اجباری (`channel_username`) برای تأیید بازیکنان.
- **alliances**: ردیابی اتحادها بین ممالک (`country1`، `country2`) برای جلوگیری از حملات و اشتراک منابع.

### ساختار کد
- **اجزای اصلی**:
  - کلاس `Database`: مدیریت عملیات پایگاه داده SQLite، از جمله ایجاد جداول، مدیریت کاربران و ذخیره وضعیت بازی.
  - هندلر `start`: شروع بازی، تأیید عضویت در کانال‌ها و نمایش منوی اصلی.
  - هندلر `panel`: ارائه رابط مدیریتی برای مدیریت تنظیمات و کاربران.
  - هندلر `button`: پردازش انتخاب‌های منوی تعاملی از طریق callback queries.
  - هندلر `message_handler`: مدیریت ورودی‌های متنی برای اقداماتی مانند تنظیم قیمت، ارسال پیام یا پردازش پرداخت‌ها.
- **متغیرهای کلیدی**:
  - `COUNTRIES`: دیکشنری ممالک موجود با وضعیت اولیه.
  - `EQUIPMENTS`: دیکشنری انواع تجهیزات با نام‌ها و قیمت‌ها (مانند ارتش، جاسوس، فایروال).
  - `ATTACK_EQUIPMENTS` و `DEFENSE_EQUIPMENTS`: لیست‌هایی که نقش تجهیزات را تعریف می‌کنند.
  - `DAMAGE_VALUES`: مکانیزم‌های آسیب برای عملیات تهاجمی.
  - `ADMIN_PERMISSIONS`: لیست دسترسی‌های مدیریتی برای کنترل دقیق.
- **طراحی ناهمگام**: استفاده از `asyncio` برای تعاملات غیرهمزمان با API تلگرام، تضمین عملکرد روان.

### مشارکت
مشارکت‌ها بسیار استقبال می‌شوند! برای مشارکت:
1. مخزن را در GitHub فورک کنید.
2. تغییرات یا ویژگی‌های جدید را در فورک خود اعمال کنید.
3. درخواست pull با توضیحات دقیق تغییرات ارسال کنید.
4. اشکالات را گزارش دهید یا پیشنهادات بهبود را از طریق ایجاد مسائل در GitHub مطرح کنید.

### مجوز
این پروژه تحت مجوز MIT منتشر شده است.

---

## 中文

### 简介
MyKingdomBot 是一个基于 Telegram 的复杂策略游戏机器人，使用 Python 语言和 `python-telegram-bot` 库开发。它提供了一个沉浸式体验，玩家可以建立和管理虚拟王国，购买战略装备，结成联盟，并对其他玩家的王国进行战术操作。该机器人使用 SQLite 进行稳健的数据持久化，并包含一个全面的管理面板用于游戏管理。支持多语言（主要为波斯语）并与 Telegram 频道集成，提供了一个动态且交互式的游戏环境。

### 主要功能
- **王国建立与管理**：玩家可以创建和管理具有独特属性和战略重要性的王国。
- **装备系统**：购买和部署各种装备，如军队、间谍、黑客、防火墙和防御盾牌，以增强游戏体验。
- **联盟系统**：与其他王国结成战略联盟，共享资源，防止相互攻击，并分享胜利奖励。
- **攻击与防御机制**：执行军事攻击、间谍活动和黑客攻击等操作，同时使用战略装备保护自己的王国。
- **管理面板**：管理员拥有广泛的控制权，可以启动/结束游戏、设置价格、管理用户等。
- **Telegram 频道整合**：支持强制加入频道以验证玩家身份，并通过 Telegram 频道广播游戏更新。
- **波斯语支持**：机器人主要以波斯语设计，并具备适配其他语言的潜力。
- **数据库驱动**：使用 SQLite 存储游戏状态，包括用户数据、王国详情、装备库存和联盟信息。

### 要求
- Python 3.8 或更高版本
- `python-telegram-bot` 库（20.0 或更高版本）
- SQLite3（包含在 Python 标准库中）
- `uuid` 库（包含在 Python 标准库中）
- 标准 Python 库：`logging`、`asyncio`、`time`、`random`

### 安装
1. 安装所需依赖项：
   ```bash
   pip install python-telegram-bot
   ```
2. 通过将代码中的 `TOKEN` 变量替换为从 BotFather 获取的机器人令牌来配置 Telegram 机器人令牌。
3. 运行脚本时会自动创建 SQLite 数据库文件（`war_game.db`）。
4. 运行机器人：
   ```bash
   python bot.py
   ```

### 使用
- **开始游戏**：在 Telegram 中发送 `/start` 命令启动机器人。
- **玩家操作**：通过交互式菜单建立王国、购买装备、结成联盟或对其他王国执行操作。
- **管理员功能**：管理员可以使用 `/panel` 命令访问管理面板，以管理游戏设置、价格、用户和广播消息。
- **频道验证**：玩家必须加入指定的 Telegram 频道以验证参与资格。
- **游戏机制**：玩家可以进行战略操作（如攻击、间谍活动），并使用防火墙和防御盾牌等装备保护王国。

### 数据库结构
机器人使用 SQLite 数据库，包含以下表：
- **users**：存储玩家信息（`user_id`、`username`、`is_banned`、`is_verified`）。
- **countries**：跟踪王国详情（`name`、`status`、`price`、`owner_id`），状态包括可用（✅）、已拥有（❌）或被摧毁（💀）。
- **equipments**：管理玩家装备库存（`user_id`、`country_name`、`equipment_id`、`quantity`）。
- **game_settings**：存储游戏配置（`key`、`value`），如游戏状态和奖励详情。
- **admins**：管理管理员权限（`user_id`、`permissions`），用于精确控制管理操作。
- **required_channels**：列出用于验证的强制 Telegram 频道（`channel_username`）。
- **alliances**：跟踪王国之间的联盟（`country1`、`country2`），以防止攻击并启用资源共享。

### 代码结构
- **主要组件**：
  - `Database` 类：处理 SQLite 数据库操作，包括表创建、用户管理和游戏状态持久化。
  - `start` 处理器：启动游戏，验证频道订阅，并显示主菜单。
  - `panel` 处理器：提供管理界面，用于管理游戏设置和用户。
  - `button` 处理器：处理交互式菜单选择的回调查询。
  - `message_handler` 处理器：处理文本输入，用于设置价格、发送消息或处理支付等操作。
- **关键变量**：
  - `COUNTRIES`：可用王国的字典，包含初始状态。
  - `EQUIPMENTS`：装备类型的字典，包含名称和价格（如军队、间谍、防火墙）。
  - `ATTACK_EQUIPMENTS` 和 `DEFENSE_EQUIPMENTS`：定义装备角色的列表。
  - `DAMAGE_VALUES`：定义攻击操作的伤害机制。
  - `ADMIN_PERMISSIONS`：列出可用的管理权限，用于精确控制。
- **异步设计**：使用 `asyncio` 进行非阻塞 Telegram API 交互，确保流畅的性能。

### 贡献
非常欢迎贡献！参与方式：
1. 在 GitHub 上叉取该仓库。
2. 在您的叉取版本中进行更改或添加新功能。
3. 提交带有详细更改说明的拉取请求。
4. 通过在 GitHub 上创建问题报告错误或提出改进建议。

### 许可
本项目采用 MIT 许可证发布。