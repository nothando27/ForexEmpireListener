import asyncio
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

from telethon import TelegramClient, events


# ============================================================
# FOREX EMPIRE TELEGRAM LISTENER - V1
# ============================================================
# V1 PURPOSE:
# - Log into Telegram using YOUR normal Telegram account
# - Monitor @Forex_Empire20
# - Display new Telegram posts
# - DOES NOT PLACE TRADES
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
        # LOGIN
        # ----------------------------------------------------

        self.log(
            "Logging into your Telegram account..."
        )

        await self.client.start(
            phone=phone
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
