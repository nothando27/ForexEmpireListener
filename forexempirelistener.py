```python
import asyncio
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError


# ============================================================
# FOREX EMPIRE TELEGRAM LISTENER - V1
# ============================================================
# V1 PURPOSE:
# - Log into Telegram using YOUR normal Telegram account
# - Monitor @Forex_Empire20
# - Display new Telegram posts
# - DOES NOT PLACE TRADES
#
# LOGIN:
# - OTP is entered through the GUI
# - Telegram 2FA password is entered through the GUI if required
# - No console/stdin is required
#
# Later versions:
# V2 = Detect XAUUSD / GOLD signals
# V3 = Extract BUY/SELL + Entry + SL + TP
# V4 = Send structured signal to MT5
# V5 = Demo trading + duplicate protection
# ============================================================


CHANNEL = "@Forex_Empire20"
SESSION_NAME = "ForexEmpireListener"


class ForexEmpireListener:

    def __init__(self, root):

        self.root = root

        self.root.title("Forex Empire Listener - V1")

        self.root.geometry("850x600")

        self.root.minsize(700, 500)

        self.client = None
        self.loop = None

        self.login_code = None
        self.login_password = None

        self.login_code_event = None
        self.login_password_event = None

        # ----------------------------------------------------
        # MAIN FRAME
        # ----------------------------------------------------

        main = ttk.Frame(root, padding=15)

        main.pack(fill="both", expand=True)

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title = ttk.Label(
            main,
            text="Forex Empire Telegram Listener",
            font=("Segoe UI", 18, "bold")
        )

        title.pack(anchor="w", pady=(0, 5))

        subtitle = ttk.Label(
            main,
            text="V1 - Telegram monitoring only. No MT5 trades.",
            font=("Segoe UI", 10)
        )

        subtitle.pack(anchor="w", pady=(0, 15))

        # ----------------------------------------------------
        # CREDENTIAL FRAME
        # ----------------------------------------------------

        credentials = ttk.LabelFrame(
            main,
            text="Telegram Login",
            padding=10
        )

        credentials.pack(fill="x")

        # API ID

        ttk.Label(
            credentials,
            text="API ID:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=5,
            pady=5
        )

        self.api_id_entry = ttk.Entry(
            credentials,
            width=45
        )

        self.api_id_entry.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=5,
            pady=5
        )

        # API HASH

        ttk.Label(
            credentials,
            text="API Hash:"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=5,
            pady=5
        )

        self.api_hash_entry = ttk.Entry(
            credentials,
            width=45,
            show="*"
        )

        self.api_hash_entry.grid(
            row=1,
            column=1,
            sticky="ew",
            padx=5,
            pady=5
        )

        # PHONE

        ttk.Label(
            credentials,
            text="Phone:"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=5,
            pady=5
        )

        self.phone_entry = ttk.Entry(
            credentials,
            width=45
        )

        self.phone_entry.insert(
            0,
            "+27"
        )

        self.phone_entry.grid(
            row=2,
            column=1,
            sticky="ew",
            padx=5,
            pady=5
        )

        credentials.columnconfigure(
            1,
            weight=1
        )

        # ----------------------------------------------------
        # CONNECT BUTTON
        # ----------------------------------------------------

        self.connect_button = ttk.Button(
            main,
            text="CONNECT TO TELEGRAM",
            command=self.start_connection
        )

        self.connect_button.pack(
            anchor="w",
            pady=12
        )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        status_frame = ttk.Frame(main)

        status_frame.pack(
            fill="x",
            pady=(0, 10)
        )

        ttk.Label(
            status_frame,
            text="Status:"
        ).pack(
            side="left"
        )

        self.status_label = ttk.Label(
            status_frame,
            text="Not connected"
        )

        self.status_label.pack(
            side="left",
            padx=8
        )

        # ----------------------------------------------------
        # MESSAGE WINDOW
        # ----------------------------------------------------

        message_frame = ttk.LabelFrame(
            main,
            text="Telegram Messages",
            padding=5
        )

        message_frame.pack(
            fill="both",
            expand=True
        )

        self.message_box = scrolledtext.ScrolledText(
            message_frame,
            wrap="word",
            font=("Consolas", 10)
        )

        self.message_box.pack(
            fill="both",
            expand=True
        )

        # ----------------------------------------------------
        # INITIAL MESSAGE
        # ----------------------------------------------------

        self.log(
            "Forex Empire Listener V1 started."
        )

        self.log(
            f"Target channel: {CHANNEL}"
        )

        self.log(
            "Waiting for Telegram connection..."
        )

    # ========================================================
    # LOGGING
    # ========================================================

    def log(self, message):

        def write():

            self.message_box.insert(
                tk.END,
                message + "\n"
            )

            self.message_box.see(
                tk.END
            )

        self.root.after(
            0,
            write
        )

    # ========================================================
    # STATUS
    # ========================================================

    def set_status(self, message):

        self.root.after(
            0,
            lambda: self.status_label.config(
                text=message
            )
        )

    # ========================================================
    # START CONNECTION
    # ========================================================

    def start_connection(self):

        try:

            api_id_text = self.api_id_entry.get().strip()

            api_hash = self.api_hash_entry.get().strip()

            phone = self.phone_entry.get().strip()

            if not api_id_text:

                raise ValueError(
                    "Please enter your Telegram API ID."
                )

            if not api_hash:

                raise ValueError(
                    "Please enter your Telegram API Hash."
                )

            if not phone:

                raise ValueError(
                    "Please enter your Telegram phone number."
                )

            api_id = int(api_id_text)

        except ValueError as error:

            messagebox.showerror(
                "Login information",
                str(error)
            )

            return

        self.connect_button.config(
            state="disabled"
        )

        self.set_status(
            "Connecting..."
        )

        self.log(
            "Starting Telegram connection..."
        )

        thread = threading.Thread(
            target=self.telegram_thread,
            args=(
                api_id,
                api_hash,
                phone
            ),
            daemon=True
        )

        thread.start()

    # ========================================================
    # TELEGRAM THREAD
    # ========================================================

    def telegram_thread(
        self,
        api_id,
        api_hash,
        phone
    ):

        self.loop = asyncio.new_event_loop()

        asyncio.set_event_loop(
            self.loop
        )

        try:

            self.loop.run_until_complete(
                self.telegram_main(
                    api_id,
                    api_hash,
                    phone
                )
            )

        except Exception as error:

            self.log(
                f"ERROR: {error}"
            )

            self.set_status(
                "Connection error"
            )

            self.root.after(
                0,
                lambda: self.connect_button.config(
                    state="normal"
                )
            )

        finally:

            try:

                self.loop.close()

            except Exception:

                pass

    # ========================================================
    # GUI LOGIN CODE
    # ========================================================

    def ask_login_code(self):

        self.login_code_event = asyncio.Event()

        self.root.after(
            0,
            self.show_login_code_window
        )

        self.login_code_event_wait()

    # ========================================================
    # WAIT FOR LOGIN CODE
    # ========================================================

    def login_code_event_wait(self):

        while not self.login_code_event.is_set():

            self.root.update()

            self.login_code_event._loop.call_soon_threadsafe(
                lambda: None
            )

            import time

            time.sleep(0.05)

    # ========================================================
    # LOGIN CODE WINDOW
    # ========================================================

    def show_login_code_window(self):

        window = tk.Toplevel(self.root)

        window.title("Telegram Login Code")

        window.geometry("420x190")

        window.resizable(False, False)

        window.transient(self.root)

        window.grab_set()

        ttk.Label(
            window,
            text="Telegram Login Code",
            font=("Segoe UI", 13, "bold")
        ).pack(
            pady=(20, 5)
        )

        ttk.Label(
            window,
            text="Enter the code Telegram sent to you:"
        ).pack(
            pady=5
        )

        code_entry = ttk.Entry(
            window,
            width=30
        )

        code_entry.pack(
            pady=8
        )

        code_entry.focus_set()

        def submit_code():

            code = code_entry.get().strip()

            if not code:

                messagebox.showerror(
                    "Login Code",
                    "Please enter the Telegram login code.",
                    parent=window
                )

                return

            self.login_code = code

            window.grab_release()

            window.destroy()

            self.root.after(
                0,
                self.set_login_code_event
            )

        ttk.Button(
            window,
            text="SUBMIT CODE",
            command=submit_code
        ).pack(
            pady=8
        )

        window.protocol(
            "WM_DELETE_WINDOW",
            window.destroy
        )

    # ========================================================
    # SET LOGIN CODE EVENT
    # ========================================================

    def set_login_code_event(self):

        if self.login_code_event:

            self.login_code_event.set()

    # ========================================================
    # REQUEST LOGIN CODE
    # ========================================================

    async def request_login_code(self):

        self.login_code = None

        self.login_code_event = asyncio.Event()

        self.root.after(
            0,
            self.show_login_code_window
        )

        while self.login_code is None:

            await asyncio.sleep(0.1)

        return self.login_code

    # ========================================================
    # GUI 2FA PASSWORD
    # ========================================================

    async def request_password(self):

        self.login_password = None

        self.login_password_event = asyncio.Event()

        self.root.after(
            0,
            self.show_password_window
        )

        while self.login_password is None:

            await asyncio.sleep(0.1)

        return self.login_password

    # ========================================================
    # 2FA PASSWORD WINDOW
    # ========================================================

    def show_password_window(self):

        window = tk.Toplevel(self.root)

        window.title("Telegram 2-Step Verification")

        window.geometry("450x200")

        window.resizable(False, False)

        window.transient(self.root)

        window.grab_set()

        ttk.Label(
            window,
            text="Telegram 2-Step Verification",
            font=("Segoe UI", 13, "bold")
        ).pack(
            pady=(20, 5)
        )

        ttk.Label(
            window,
            text="Enter your Telegram 2FA password:"
        ).pack(
            pady=5
        )

        password_entry = ttk.Entry(
            window,
            width=32,
            show="*"
        )

        password_entry.pack(
            pady=8
        )

        password_entry.focus_set()

        def submit_password():

            password = password_entry.get()

            if not password:

                messagebox.showerror(
                    "Telegram Password",
                    "Please enter your Telegram 2FA password.",
                    parent=window
                )

                return

            self.login_password = password

            window.grab_release()

            window.destroy()

        ttk.Button(
            window,
            text="SUBMIT PASSWORD",
            command=submit_password
        ).pack(
            pady=8
        )

        window.protocol(
            "WM_DELETE_WINDOW",
            window.destroy
        )

    # ========================================================
    # TELEGRAM MAIN
    # ========================================================

    async def telegram_main(
        self,
        api_id,
        api_hash,
        phone
    ):

        self.client = TelegramClient(
            SESSION_NAME,
            api_id,
            api_hash
        )

        self.log(
            "Connecting to Telegram..."
        )

        # ----------------------------------------------------
        # NEW MESSAGE HANDLER
        # ----------------------------------------------------

        @self.client.on(
            events.NewMessage(
                chats=CHANNEL
            )
        )
        async def new_message_handler(event):

            message_text = event.raw_text or ""

            self.log("")

            self.log(
                "========================================"
            )

            self.log(
                "NEW TELEGRAM POST"
            )

            self.log(
                "========================================"
            )

            self.log(
                message_text
            )

            self.log(
                "========================================"
            )

            # ------------------------------------------------
            # V1 ONLY DISPLAYS THE MESSAGE.
            #
            # NO TRADING CODE HERE.
            # ------------------------------------------------

        # ----------------------------------------------------
        # CONNECT
        # ----------------------------------------------------

        await self.client.connect()

        # ----------------------------------------------------
        # CHECK EXISTING SESSION
        # ----------------------------------------------------

        if await self.client.is_user_authorized():

            self.log(
                "Existing Telegram session found."
            )

        else:

            self.log(
                "No existing Telegram session found."
            )

            self.log(
                "Sending login code to Telegram..."
            )

            await self.client.send_code_request(
                phone
            )

            self.log(
                "Telegram login code sent."
            )

            # ------------------------------------------------
            # ASK FOR OTP THROUGH GUI
            # ------------------------------------------------

            code = await self.request_login_code()

            self.log(
                "Login code received from GUI."
            )

            try:

                await self.client.sign_in(
                    phone=phone,
                    code=code
                )

            except SessionPasswordNeededError:

                self.log(
                    "Telegram 2-step verification is enabled."
                )

                self.log(
                    "Waiting for 2FA password..."
                )

                password = await self.request_password()

                await self.client.sign_in(
                    password=password
                )

        # ----------------------------------------------------
        # GET USER INFORMATION
        # ----------------------------------------------------

        me = await self.client.get_me()

        first_name = getattr(
            me,
            "first_name",
            ""
        )

        username = getattr(
            me,
            "username",
            ""
        )

        if username:

            account_name = (
                f"{first_name} (@{username})"
            )

        else:

            account_name = first_name

        self.set_status(
            "CONNECTED"
        )

        self.log("")

        self.log(
            "========================================"
        )

        self.log(
            "TELEGRAM CONNECTION SUCCESSFUL"
        )

        self.log(
            f"Logged in as: {account_name}"
        )

        self.log(
            f"Monitoring: {CHANNEL}"
        )

        self.log(
            "Waiting for new posts..."
        )

        self.log(
            "========================================"
        )

        # ----------------------------------------------------
        # KEEP LISTENER RUNNING
        # ----------------------------------------------------

        await self.client.run_until_disconnected()


# ============================================================
# PROGRAM START
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    application = ForexEmpireListener(
        root
    )

    root.mainloop()
```
