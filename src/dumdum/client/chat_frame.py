from __future__ import annotations

import collections
import concurrent.futures
import time
from tkinter import Event, Menu, StringVar
from tkinter.ttk import Button, Entry, Frame, Label, Treeview
from typing import ContextManager

from dumdum.protocol import (
    Channel,
    ClientEvent,
    ClientEventChannelsListed,
    ClientEventMessageReceived,
    ClientEventMessagesListed,
    Message,
)

from .app import TkApp
from .scrollable_frame import ScrollableFrame
from .store import ClientStore


class ChatFrame(Frame):
    _connection_attempt: concurrent.futures.Future[None] | None

    def __init__(self, app: TkApp):
        super().__init__(padding=10)

        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=4)
        self.grid_rowconfigure(0, weight=1)

        self.channels: list[Channel] = []
        self.message_cache = MessageCache(max_messages=1000)

        self.channel_list = ChannelList(self)
        self.channel_list.grid(row=0, column=0, rowspan=2, padx=(0, 10), sticky="nesw")
        self.messages = MessageList(self)
        self.messages.grid(row=0, column=1, sticky="nesw")
        self.send_box = SendBox(self)
        self.send_box.grid(row=1, column=1, sticky="nesw", pady=(10, 0))

    def handle_client_event(self, event: ClientEvent) -> None:
        if isinstance(event, ClientEventChannelsListed):
            self.channels.clear()
            self.channels.extend(event.channels)
            self.channel_list.refresh()

            for channel in event.channels:
                coro = self.app.client.list_messages(channel.name)
                self.app.submit(coro)

        elif isinstance(event, ClientEventMessageReceived):
            self.add_message(event.message)
        elif isinstance(event, ClientEventMessagesListed):
            for message in event.messages:
                self.add_message(message)

    def add_message(self, message: Message) -> None:
        self.message_cache.add_message(message)
        channel = self.get_channel(message.channel_name)
        if channel == self.channel_list.selected_channel:
            self.messages.add_message(message)

    def get_channel(self, name: str) -> Channel | None:
        for channel in self.channels:
            if channel.name == name:
                return channel


class ChannelList(Frame):
    def __init__(self, parent: ChatFrame) -> None:
        super().__init__(parent)

        self.parent = parent

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tree = Treeview(self, selectmode="browse", show="tree")
        self.tree.grid(sticky="nesw")

        # TODO: maybe add button to refresh channels?

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    @property
    def store(self) -> ContextManager[ClientStore]:
        return self.parent.app.store_factory()

    @property
    def addr(self) -> str:
        return self.parent.app.client.addr

    @property
    def selected_channel(self) -> Channel | None:
        selection = self.tree.selection()
        if len(selection) < 1:
            return None

        return self.parent.get_channel(selection[0])

    def refresh(self) -> None:
        selection = self.tree.selection()
        self.tree.delete(*self.tree.get_children())

        for channel in self.parent.channels:
            self.tree.insert("", "end", channel.name, text=channel.name)

        children = self.tree.get_children()
        if len(selection) == 0 and len(children) > 0:
            with self.store as store:
                last = store.get_last_selected_channel(self.addr)
                if last is None or last not in children:
                    last = children[0]
                self.tree.selection_set(last)

    def _on_tree_select(self, event: Event) -> None:
        selected_channel = self.selected_channel

        with self.store as store:
            name = selected_channel and selected_channel.name
            store.set_last_selected_channel(self.addr, name)

        self.parent.messages.set_channel(selected_channel)


class MessageList(Frame):
    UPDATE_RATE = 250
    UPDATE_IDLE_PERIOD = 0.75

    _last_configured: float | None

    def __init__(self, parent: ChatFrame):
        super().__init__(parent, borderwidth=1, relief="solid")

        self.parent = parent

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.messages: list[MessageView] = []

        self._scroll_frame = ScrollableFrame(
            self,
            xscroll=True,
            yscroll=True,
            autoscroll=True,
        )
        canvas = self._scroll_frame.grid_slaves(0, 0)[0]
        canvas.grid(padx=10, pady=10)
        self._scroll_frame.grid(row=0, column=0, sticky="nesw")

        self._last_configured = None
        self.after(self.UPDATE_RATE, self._update_loop)

        self.bind("<Configure>", self._on_configure)

    def add_message(self, message: Message) -> None:
        widget = MessageView(self._scroll_frame.inner, self, message)
        widget.wrap_to_width(self.winfo_width())
        widget.grid(row=len(self.messages), column=0, sticky="ew")
        self.messages.append(widget)

    def clear_messages(self) -> list[MessageView]:
        messages = self.messages.copy()
        self.messages.clear()

        for message in messages:
            message.grid_forget()

        return messages

    def set_channel(self, channel: Channel | None) -> None:
        self.clear_messages()

        if channel is not None:
            for message in self.parent.message_cache.get_messages(channel):
                self.add_message(message)

    def _on_configure(self, event: Event) -> None:
        self._last_configured = time.perf_counter()

    def _update_loop(self) -> None:
        self.after(self.UPDATE_RATE, self._update_loop)

        if self._last_configured is None:
            return
        elif time.perf_counter() < self._last_configured + self.UPDATE_IDLE_PERIOD:
            return

        self._last_configured = None
        for message in self.messages:
            message.wrap_to_width(self.winfo_width())


class MessageView(Frame):
    def __init__(self, frame: Frame, parent: MessageList, message: Message) -> None:
        super().__init__(frame)

        self.parent = parent
        self.message = message

        self.nick = Label(self, text=f"{message.nick}:", font="bold 10")
        self.nick.grid(row=0, column=0, sticky="nw")
        self.content = Label(self, text=message.content, wraplength=1000)
        self.content.grid(row=0, column=1, sticky="ew")

    def wrap_to_width(self, width: int) -> None:
        minimum = 800
        maximum = width - self.nick.winfo_reqwidth() - 20
        self.content.configure(wraplength=max(minimum, maximum))


class MessageCache:
    _channel_messages: dict[str, collections.deque[Message]]

    def __init__(self, *, max_messages: int) -> None:
        self.max_messages = max_messages
        self._channel_messages = collections.defaultdict(self._create_message_queue)

    def add_message(self, message: Message) -> None:
        self._channel_messages[message.channel_name].append(message)

    def get_messages(self, channel: Channel) -> list[Message]:
        messages = self._channel_messages.get(channel.name)
        if messages is None:
            return []
        return list(messages)

    def _create_message_queue(self) -> collections.deque[Message]:
        return collections.deque(maxlen=self.max_messages)


class SendBox(Frame):
    def __init__(self, parent: ChatFrame) -> None:
        super().__init__(parent)

        self.parent = parent

        self.grid_columnconfigure(0, weight=1)

        self.content_entry_var = StringVar(self)
        self.content_entry = Entry(self, textvariable=self.content_entry_var)
        self.content_entry.grid(row=0, column=0, sticky="ew")
        self.send_button = Button(self, text="Send", command=self.do_send)
        self.send_button.grid(row=0, column=1)

        self.content_entry.bind("<Return>", lambda event: self.do_send())

    def do_send(self) -> None:
        content = self.content_entry_var.get()
        if len(content) < 1:
            return

        channel = self.parent.channel_list.selected_channel
        if channel is None:
            return

        self.content_entry_var.set("")
        coro = self.parent.app.client.send_message(channel.name, content)
        self.parent.app.submit(coro)


class ChatMenu(Menu):
    def __init__(self, parent: TkApp) -> None:
        super().__init__(parent)

        self.parent = parent

        self.connection = Menu(self)
        self.connection.add_command(label="Disconnect", command=self.do_disconnect)

        self.add_cascade(label="Connection", menu=self.connection)

    def do_disconnect(self) -> None:
        self.parent.disconnect()
