from __future__ import annotations
import collections

import concurrent.futures
from dataclasses import dataclass
from tkinter import Event, StringVar
from tkinter.ttk import Button, Entry, Frame, Label, Treeview

from dumdum.protocol import (
    Channel,
    ClientEvent,
    ClientEventChannelsListed,
    ClientEventMessageReceived,
)

from .app import TkApp
from .scrollable_frame import ScrollableFrame


class ChatFrame(Frame):
    _connection_attempt: concurrent.futures.Future[None] | None

    def __init__(self, app: TkApp):
        super().__init__(padding=10)

        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=4)
        self.grid_rowconfigure(0, weight=1)

        self.channels: list[Channel] = []
        self.message_cache = MessageCache()

        self.channel_list = ChannelList(self)
        self.channel_list.grid(row=0, column=0, rowspan=2, sticky="nesw")
        self.messages = MessageList(self)
        self.messages.grid(row=0, column=1, sticky="nesw")
        self.send_box = SendBox(self)
        self.send_box.grid(row=1, column=1, sticky="nesw")

    def handle_client_event(self, event: ClientEvent) -> None:
        if isinstance(event, ClientEventChannelsListed):
            self.channels.clear()
            self.channels.extend(event.channels)
            self.channel_list.refresh()
        elif isinstance(event, ClientEventMessageReceived):
            message = self.message_cache.add_message_from_event(event)
            self.messages.add_message(message)


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
    def selected_channel(self) -> Channel | None:
        selection = self.tree.selection()
        if len(selection) < 1:
            return None

        name = selection[0]
        for channel in self.parent.channels:
            if channel.name == name:
                return channel

    def refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())

        for channel in self.parent.channels:
            self.tree.insert("", "end", channel.name, text=channel.name)

    def _on_tree_select(self, event: Event) -> None:
        self.parent.messages.set_channel(self.selected_channel)


class MessageList(ScrollableFrame):
    def __init__(self, parent: ChatFrame):
        super().__init__(parent)

        self.parent = parent

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.messages: list[MessageView] = []

    def add_message(self, message: Message) -> None:
        widget = MessageView(self.inner, self, message)
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


class MessageView(Frame):
    def __init__(self, frame: Frame, parent: MessageList, message: Message) -> None:
        super().__init__(frame)

        self.parent = parent
        self.message = message

        self.nick = Label(self, text=message.nick)
        self.nick.grid(row=0, column=0, sticky="w")
        self.content = Label(self, text=message.content, wraplength=1000)
        self.content.grid(row=1, column=0, sticky="ew")


@dataclass
class Message:
    nick: str
    content: str


class MessageCache:
    def __init__(self) -> None:
        self.channel_messages: dict[str, list[Message]] = collections.defaultdict(list)

    def add_message(self, channel: Channel, message: Message) -> None:
        self.channel_messages[channel.name].append(message)

    def add_message_from_event(self, event: ClientEventMessageReceived) -> Message:
        message = Message(event.nick, event.content)
        self.add_message(event.channel, message)
        return message

    def get_messages(self, channel: Channel) -> list[Message]:
        messages = self.channel_messages.get(channel.name)
        if messages is None:
            return []
        return messages.copy()


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