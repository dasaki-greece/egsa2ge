import os
import sys
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from typing import Optional
from ttkbootstrap.widgets import ToolTip
from PIL import Image, ImageTk
from ttkbootstrap.scrolled import ScrolledFrame


class TopmostToolTip(ToolTip):
    def show_tip(self, *args, **kwargs):
        super().show_tip(*args, **kwargs)
        if self.toplevel:
            self.toplevel.attributes("-topmost", True)


from ..utils.platform_utils import (
    is_google_earth_installed,
    is_google_earth_running,
    launch_google_earth_empty,
)

from ..models import PointModel
from ..core.coordinates import transform_egsa87_to_wgs84
from ..services.google_earth_service import GoogleEarthService
from ..config import APP_TITLE, APP_EXE_NAME, APP_VERSION


class MainWindow(ttkb.Window):
    def __init__(self, service: GoogleEarthService) -> None:
        super().__init__(themename="flatly")
        self.service = service
        self.title(f"{APP_TITLE} v{APP_VERSION}")

        try:
            if getattr(sys, "frozen", False):
                self.assets_dir = Path(sys._MEIPASS) / "assets"
            else:
                self.assets_dir = (
                    Path(__file__).resolve().parent.parent.parent.parent / "assets"
                )

            # Χρήση του favico.ico με την iconbitmap που λειτουργεί καλύτερα στα Windows
            ico_path = self.assets_dir / "favico.ico"
            if ico_path.exists():
                self.iconbitmap(str(ico_path))
        except Exception as e:
            print(f"Failed to load application icon: {e}")
            self.assets_dir = Path(__file__).resolve().parent.parent.parent.parent / "assets"

        # UI Constants
        self.PORTRAIT_WIDTH = 420
        self.DRAWER_WIDTH = 340
        self.EXPANDED_WIDTH = self.PORTRAIT_WIDTH + self.DRAWER_WIDTH
        self.WINDOW_HEIGHT = 740
        self.ANIMATION_SPEED = 15  # ms per frame
        self.ANIMATION_STEP = 80  # px per frame

        self.geometry(f"{self.PORTRAIT_WIDTH}x{self.WINDOW_HEIGHT}")
        self.resizable(True, True)
        self.minsize(self.PORTRAIT_WIDTH, 600)

        # Κρατάει το παράθυρο πάντα μπροστά (always on top)
        self.is_pinned = True
        self.attributes("-topmost", self.is_pinned)

        self.drawer_open = False
        self._animation_job = None
        self.has_opened_link = False

        self.ge_icon = self.load_button_icon("google_earth_icon.png", size=(20, 20))
        self.gm_icon = self.load_button_icon("google_maps_icon.png", size=(20, 20))

        self._build_ui()
        self.service.set_camera_callback(self.on_camera_update_threadsafe)
        self.service.initialize()

        try:
            default_point = self.parse_inputs()
            self.service.update_all_kmls(default_point)
        except Exception:
            self.service.update_all_kmls()



    def load_button_icon(self, filename: str, size=(20, 20)) -> Optional[ImageTk.PhotoImage]:
        try:
            img_path = self.assets_dir / filename
            if img_path.exists():
                pil_img = Image.open(img_path)
                pil_img = pil_img.resize(size, Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(pil_img)
        except Exception as e:
            print(f"Failed to load button icon {filename}: {e}")
        return None

    def on_camera_update_threadsafe(self, point: PointModel) -> None:
        self.after(0, self.update_inputs_from_camera, point)

    def update_inputs_from_camera(self, point: PointModel) -> None:
        if not (94875 <= point.x <= 892934) or not (3859446 <= point.y <= 4631226):
            self.target_xy_var.set("GE εκτός Ελλάδας")
            self.status_var.set(f"Λήψη από GE: Εκτός ορίων ΕΓΣΑ87")
        else:
            self.target_xy_var.set(f"{point.x:.2f}, {point.y:.2f}")
            self.status_var.set(f"Λήψη από GE: X={point.x:.2f}, Y={point.y:.2f}")

    def _build_ui(self) -> None:
        self.main_shell = ttkb.Frame(self)
        self.main_shell.pack(fill=BOTH, expand=YES)

        # Phone Frame (Left)
        self.phone_frame = ttkb.Frame(self.main_shell, width=self.PORTRAIT_WIDTH)
        self.phone_frame.pack(side=LEFT, fill=Y, expand=False)
        self.phone_frame.pack_propagate(False)

        # Separator
        sep = ttkb.Separator(self.main_shell, orient=VERTICAL)
        sep.pack(side=LEFT, fill=Y)

        # Drawer Frame (Right)
        # By setting a fixed width and disabling propagation, the contents inside
        # won't reflow or stretch during the animation. They will simply be revealed.
        self.drawer_frame = ttkb.Frame(self.main_shell, width=self.DRAWER_WIDTH)
        self.drawer_frame.pack(side=LEFT, fill=Y, expand=False)
        self.drawer_frame.pack_propagate(False)

        self.build_main_view()
        self.build_drawer_view()
        self._update_wgs84_preview()
        self.check_ge_status()

    def build_main_view(self) -> None:
        self.build_status_bar()

        actions_frame = ttkb.Frame(self.phone_frame, padding=15)
        actions_frame.pack(fill=X, side=BOTTOM, pady=(0, 0))

        btn_ge = ttkb.Button(
            actions_frame,
            text="  Προβολή στο Google Earth",
            image=self.ge_icon,
            compound=LEFT,
            command=self.goto_point,
            bootstyle=PRIMARY,
            padding=10,
        )
        btn_ge.pack(fill=X, pady=(0, 10))
        TopmostToolTip(
            btn_ge,
            text="Μετάβαση και εστίαση της κάμερας στο σημείο αυτό στο Google Earth",
            bootstyle=(PRIMARY, INVERSE),
        )

        btn_gm = ttkb.Button(
            actions_frame,
            text="  Προβολή στους Χάρτες Google",
            image=self.gm_icon,
            compound=LEFT,
            command=self.open_google_maps,
            bootstyle=PRIMARY,
            padding=10,
        )
        btn_gm.pack(fill=X)
        TopmostToolTip(
            btn_gm,
            text="Άνοιγμα του σημείου στους Χάρτες Google στον περιηγητή ιστού",
            bootstyle=(PRIMARY, INVERSE),
        )

        header = ttkb.Frame(self.phone_frame, padding=10)
        header.pack(fill=X, pady=(5, 0))

        title_lbl = ttkb.Label(
            header,
            text="ΕΓΣΑ ’87 → GE",
            font=("Segoe UI", 16, "bold"),
            bootstyle=PRIMARY,
        )
        title_lbl.pack(side=LEFT, anchor=W)

        version_lbl = ttkb.Label(
            header,
            text=f"v{APP_VERSION}",
            font=("Segoe UI", 9),
            bootstyle=SECONDARY,
        )
        version_lbl.pack(side=LEFT, anchor=S, padx=(5, 0), pady=(0, 4))

        self.toggle_btn = ttkb.Button(
            header,
            text="☰",
            bootstyle=(PRIMARY, OUTLINE),
            command=self.toggle_drawer,
            width=3,
        )
        self.toggle_btn.pack(side=RIGHT)
        TopmostToolTip(
            self.toggle_btn,
            text="Εμφάνιση/Απόκρυψη πλευρικού μενού",
            bootstyle=(PRIMARY, INVERSE),
        )

        self.pin_btn = ttkb.Button(
            header,
            text="📌",
            bootstyle=DANGER,  # Solid color shows active pinned state at startup
            command=self.toggle_pin,
            width=3,
        )
        self.pin_btn.pack(side=RIGHT, padx=(0, 5))
        TopmostToolTip(
            self.pin_btn,
            text="Καρφίτσωμα παραθύρου (Πάντα στην κορυφή)",
            bootstyle=(DANGER, INVERSE),
        )

        desc_lbl = ttkb.Label(
            self.phone_frame,
            text="Μετατροπή ΕΓΣΑ ’87 σε WGS84\nκαι δυναμική μετάβαση στο Google Earth",
            font=("Segoe UI", 9),
            bootstyle=SECONDARY,
            justify=LEFT,
        )
        desc_lbl.pack(fill=X, padx=15, pady=(0, 15))

        input_card = ttkb.Labelframe(
            self.phone_frame, text="Στοιχεία Σημείου", padding=15, bootstyle=PRIMARY
        )
        input_card.pack(fill=X, padx=15, pady=(0, 15))
        input_card.columnconfigure(1, weight=1)

        self.x_var = ttkb.StringVar(value="373306.33")
        self.y_var = ttkb.StringVar(value="4457763.39")
        self.name_var = ttkb.StringVar(value="Σημείο ΕΓΣΑ87")
        self.range_var = ttkb.StringVar(value="800")

        lbl_x = ttkb.Label(input_card, text="Χ (Easting) ⓘ:", font=("", 10, "bold"))
        lbl_x.grid(row=0, column=0, sticky=W, pady=5, padx=(0, 10))
        TopmostToolTip(
            lbl_x,
            text="Συντεταγμένη Easting (Ανατολή) σε μέτρα στο σύστημα ΕΓΣΑ'87.\nΈγκυρο εύρος για την Ελλάδα: 94.875 έως 892.934.",
            bootstyle=(PRIMARY, INVERSE),
        )

        self.x_ent = ttkb.Entry(input_card, textvariable=self.x_var)
        self.x_ent.grid(row=0, column=1, sticky=EW, pady=5)
        self.x_ent.bind("<KeyRelease>", self._update_wgs84_preview)

        lbl_y = ttkb.Label(input_card, text="Υ (Northing) ⓘ:", font=("", 10, "bold"))
        lbl_y.grid(row=1, column=0, sticky=W, pady=5, padx=(0, 10))
        TopmostToolTip(
            lbl_y,
            text="Συντεταγμένη Northing (Βορράς) σε μέτρα στο σύστημα ΕΓΣΑ'87.\nΈγκυρο εύρος για την Ελλάδα: 3.859.446 έως 4.631.226.",
            bootstyle=(PRIMARY, INVERSE),
        )

        self.y_ent = ttkb.Entry(input_card, textvariable=self.y_var)
        self.y_ent.grid(row=1, column=1, sticky=EW, pady=5)
        self.y_ent.bind("<KeyRelease>", self._update_wgs84_preview)

        lbl_name = ttkb.Label(input_card, text="Όνομα ⓘ:")
        lbl_name.grid(row=2, column=0, sticky=W, pady=5, padx=(0, 10))
        TopmostToolTip(
            lbl_name,
            text="Το όνομα/ετικέτα που θα έχει το σημείο κατά την προβολή του στο Google Earth.",
            bootstyle=(PRIMARY, INVERSE),
        )

        ttkb.Entry(input_card, textvariable=self.name_var).grid(
            row=2, column=1, sticky=EW, pady=5
        )

        lbl_range = ttkb.Label(input_card, text="Απόσταση (m) ⓘ:")
        lbl_range.grid(row=3, column=0, sticky=W, pady=5, padx=(0, 10))
        TopmostToolTip(
            lbl_range,
            text="Το υψόμετρο/απόσταση της κάμερας από το έδαφος στο Google Earth.\nΠ.χ. 100 για κοντινή εστίαση, 1000 για γενική εποπτεία.",
            bootstyle=(PRIMARY, INVERSE),
        )

        ttkb.Entry(input_card, textvariable=self.range_var).grid(
            row=3, column=1, sticky=EW, pady=5
        )

        self.target_card = ttkb.Labelframe(
            self.phone_frame, text="Στόχος X,Y ⓘ", padding=15, bootstyle=SECONDARY
        )
        self.target_card.pack(fill=X, padx=15, pady=(0, 15))
        self.target_card.columnconfigure(0, weight=4)
        self.target_card.columnconfigure(1, weight=1)
        TopmostToolTip(
            self.target_card,
            text="Οι συντεταγμένες ΕΓΣΑ'87 του κέντρου της κάμερας στο Google Earth (Camera Tracking).\nΕνημερώνονται αυτόματα καθώς μετακινείστε στον χάρτη.",
            bootstyle=(SECONDARY, INVERSE),
        )

        self.target_xy_var = ttkb.StringVar(value="GE Εκτός σύνδεσης")

        target_lbl = ttkb.Label(
            self.target_card,
            textvariable=self.target_xy_var,
            anchor=CENTER,
            font=("", 11, "bold"),
        )
        target_lbl.grid(row=0, column=0, sticky=EW, pady=5, padx=(0, 5))

        copy_btn = ttkb.Button(
            self.target_card,
            text="📋",
            bootstyle=(PRIMARY, OUTLINE),
            command=self.copy_target_xy,
        )
        copy_btn.grid(row=0, column=1, sticky=EW, pady=5)
        TopmostToolTip(
            copy_btn,
            text="Αντιγραφή συντεταγμένων στόχου στο πρόχειρο",
            bootstyle=(PRIMARY, INVERSE),
        )

        wgs_card = ttkb.Labelframe(
            self.phone_frame, text="Αποτέλεσμα WGS84 ⓘ", padding=15, bootstyle=SECONDARY
        )
        wgs_card.pack(fill=X, padx=15, pady=(0, 15))
        wgs_card.columnconfigure(1, weight=1)
        TopmostToolTip(
            wgs_card,
            text="Οι συντεταγμένες μετατραμμένες στο παγκόσμιο σύστημα WGS84 (Γεωγραφικό Πλάτος/Μήκος).\nΚατάλληλο για χρήση σε GPS, Google Maps κ.λπ.",
            bootstyle=(SECONDARY, INVERSE),
        )

        self.lat_var = ttkb.StringVar(value="-")
        self.lon_var = ttkb.StringVar(value="-")
        self.kml_fmt_var = ttkb.StringVar(value="-")

        ttkb.Label(wgs_card, text="Latitude:", font=("", 10, "bold")).grid(
            row=0, column=0, sticky=W, pady=2, padx=(0, 10)
        )
        lat_ent = ttkb.Entry(
            wgs_card,
            textvariable=self.lat_var,
            font=("", 10),
            state="readonly",
        )
        lat_ent.grid(row=0, column=1, sticky=EW, pady=2)

        ttkb.Label(wgs_card, text="Longitude:", font=("", 10, "bold")).grid(
            row=1, column=0, sticky=W, pady=2, padx=(0, 10)
        )
        lon_ent = ttkb.Entry(
            wgs_card,
            textvariable=self.lon_var,
            font=("", 10),
            state="readonly",
        )
        lon_ent.grid(row=1, column=1, sticky=EW, pady=2)

        ttkb.Label(wgs_card, text="KML:", font=("", 10, "bold")).grid(
            row=2, column=0, sticky=W, pady=2, padx=(0, 10)
        )
        kml_ent = ttkb.Entry(
            wgs_card,
            textvariable=self.kml_fmt_var,
            font=("", 10),
            state="readonly",
        )
        kml_ent.grid(row=2, column=1, sticky=EW, pady=2)

    def build_status_bar(self) -> None:
        self.status_var = ttkb.StringVar(value="Έτοιμο.")
        status_frame = ttkb.Frame(self.phone_frame, bootstyle=SECONDARY)
        status_frame.pack(side=BOTTOM, fill=X)

        status_bar = ttkb.Label(
            status_frame,
            textvariable=self.status_var,
            bootstyle=(INVERSE, SECONDARY),
            padding=5,
            font=("", 9),
        )
        status_bar.pack(side=LEFT, fill=X, expand=YES)

    def build_drawer_view(self) -> None:
        content = ScrolledFrame(self.drawer_frame, padding=20, autohide=True)
        content.pack(fill=BOTH, expand=YES)

        header = ttkb.Frame(content)
        header.pack(fill=X, pady=(0, 20))

        ttkb.Label(header, text="Εργαλεία", font=("Segoe UI", 14, "bold")).pack(
            side=LEFT
        )
        ttkb.Button(
            header,
            text="❮",
            bootstyle=(SECONDARY, OUTLINE),
            command=self.close_drawer,
            width=3,
        ).pack(side=RIGHT)

        btn_add_saved = ttkb.Button(
            content,
            text="Προσθήκη σε μόνιμα σημεία",
            command=self.add_saved_point,
            bootstyle=PRIMARY,
            padding=8,
        )
        btn_add_saved.pack(fill=X, pady=(0, 10))
        TopmostToolTip(
            btn_add_saved,
            text="Αποθήκευση του τρέχοντος σημείου ως μόνιμο Placemark στο Google Earth (στα 'Μέρη μου')",
            bootstyle=(PRIMARY, INVERSE),
        )

        btn_copy_wgs = ttkb.Button(
            content,
            text="Αντιγραφή WGS84",
            command=self.copy_wgs84,
            bootstyle=SECONDARY,
            padding=8,
        )
        btn_copy_wgs.pack(fill=X, pady=(0, 10))
        TopmostToolTip(
            btn_copy_wgs,
            text="Αντιγραφή των συντεταγμένων WGS84 (lat, lon) στο πρόχειρο",
            bootstyle=(SECONDARY, INVERSE),
        )

        # ttkb.Button(
        #     content,
        #     text="Άνοιγμα φακέλου εργασίας",
        #     command=self.open_work_dir,
        #     bootstyle=INFO,
        #     padding=8,
        # ).pack(fill=X, pady=(0, 20))

        ttkb.Label(content, text="Πληροφορίες", font=("Segoe UI", 12, "bold")).pack(
            anchor=W, pady=(20, 10)
        )

        ttkb.Label(
            content,
            text=APP_EXE_NAME,
            font=("Segoe UI", 10, "normal"),
            bootstyle=INFO,
        ).pack(anchor=W, pady=(0, 5))

        ttkb.Label(
            content,
            text=(
                "Η εφαρμογή ΕΓΣΑ ’87 → Google Earth αναπτύχθηκε ως βοηθητικό εργαλείο "
                "μετατροπής συντεταγμένων και δυναμικής μετάβασης σε σημεία ενδιαφέροντος "
                "στο Google Earth ή Google Maps.\n\n"
                "© 2026 dasaki.gr "
            ),
            font=("", 10),
            wraplength=280,
            justify=LEFT,
        ).pack(anchor=W, pady=(0, 10))

        self.drawer_image = None
        try:
            import sys

            if getattr(sys, "frozen", False):
                assets_dir = Path(sys._MEIPASS) / "assets"
            else:
                assets_dir = (
                    Path(__file__).resolve().parent.parent.parent.parent / "assets"
                )

            img_path = assets_dir / "icon03.png"
            if img_path.exists():
                pil_img = Image.open(img_path)
                # Resize image to fit inside the 340px drawer nicely
                target_width = 260
                w_percent = target_width / float(pil_img.size[0])
                target_height = int((float(pil_img.size[1]) * float(w_percent)))
                pil_img = pil_img.resize(
                    (target_width, target_height), Image.Resampling.LANCZOS
                )

                self.drawer_image = ImageTk.PhotoImage(pil_img)

                img_lbl = ttkb.Label(content, image=self.drawer_image)
                # Using side=BOTTOM pushes the image to the bottom of the drawer
                img_lbl.pack(side=BOTTOM, pady=20)
        except Exception as e:
            print(f"Failed to load drawer image: {e}")

    def toggle_drawer(self) -> None:
        if self.drawer_open:
            self.close_drawer()
        else:
            self.open_drawer()

    def toggle_pin(self) -> None:
        self.is_pinned = not self.is_pinned
        self.attributes("-topmost", self.is_pinned)
        if self.is_pinned:
            self.lift()
            self.pin_btn.configure(bootstyle=DANGER)
        else:
            self.pin_btn.configure(bootstyle=(SECONDARY, OUTLINE))

    def open_drawer(self) -> None:
        if self.drawer_open:
            return
        self.drawer_open = True
        self.animate_drawer(self.EXPANDED_WIDTH)
        self.toggle_btn.configure(bootstyle=PRIMARY)

    def close_drawer(self) -> None:
        if not self.drawer_open:
            return
        self.drawer_open = False
        self.animate_drawer(self.PORTRAIT_WIDTH)
        self.toggle_btn.configure(bootstyle=(PRIMARY, OUTLINE))

    def animate_drawer(self, target_width: int) -> None:
        if self._animation_job is not None:
            self.after_cancel(self._animation_job)
            self._animation_job = None

        current_width = self.winfo_width()

        if current_width == target_width:
            return

        step = (
            self.ANIMATION_STEP
            if target_width > current_width
            else -self.ANIMATION_STEP
        )
        new_width = current_width + step

        if (step > 0 and new_width >= target_width) or (
            step < 0 and new_width <= target_width
        ):
            new_width = target_width
            self.geometry(f"{new_width}x{self.winfo_height()}")
        else:
            self.geometry(f"{new_width}x{self.winfo_height()}")
            self._animation_job = self.after(
                self.ANIMATION_SPEED, self.animate_drawer, target_width
            )

    def _update_wgs84_preview(self, event=None) -> None:
        try:
            x_str = self.x_var.get().replace(",", ".").strip()
            y_str = self.y_var.get().replace(",", ".").strip()
            if not x_str or not y_str:
                self.lat_var.set("-")
                self.lon_var.set("-")
                self.kml_fmt_var.set("-")
                return
            x = float(x_str)
            y = float(y_str)
            if not (94875 <= x <= 892934) or not (3859446 <= y <= 4631226):
                self.lat_var.set("Εκτός ορίων Ελλάδας")
                self.lon_var.set("Εκτός ορίων Ελλάδας")
                self.kml_fmt_var.set("-")
                return
            wgs = transform_egsa87_to_wgs84(x, y)
            self.lat_var.set(f"{wgs.latitude:.8f}")
            self.lon_var.set(f"{wgs.longitude:.8f}")
            self.kml_fmt_var.set(f"{wgs.longitude:.8f},{wgs.latitude:.8f},0")
        except ValueError:
            self.lat_var.set("Μη έγκυροι αριθμοί")
            self.lon_var.set("-")
            self.kml_fmt_var.set("-")
        except Exception:
            pass

    def check_ge_status(self) -> None:
        try:
            import time
            running = is_google_earth_running()
            last_poll = getattr(self.service, "last_poll_time", 0.0)
            online = running and (time.time() - last_poll <= 5.0)
            
            self.target_card.configure(text="Στόχος X,Y ⓘ")
            if online:
                if self.target_xy_var.get() == "GE Εκτός σύνδεσης":
                    self.target_xy_var.set("-")
            else:
                self.target_xy_var.set("GE Εκτός σύνδεσης")
        except Exception:
            pass
        self.after(2000, self.check_ge_status)

    def parse_inputs(self) -> PointModel:
        try:
            x_str = self.x_var.get().replace(",", ".").strip()
            if not x_str:
                raise ValueError("Το πεδίο Χ είναι κενό.")
            x = float(x_str)
            if not (94875 <= x <= 892934):
                raise ValueError("Εκτός ορίων Ελλάδας (94.875 - 892.934)")
        except ValueError as exc:
            raise ValueError(f"Άκυρο Χ: {exc}") from exc

        try:
            y_str = self.y_var.get().replace(",", ".").strip()
            if not y_str:
                raise ValueError("Το πεδίο Υ είναι κενό.")
            y = float(y_str)
            if not (3859446 <= y <= 4631226):
                raise ValueError("Εκτός ορίων Ελλάδας (3.859.446 - 4.631.226)")
        except ValueError as exc:
            raise ValueError(f"Άκυρο Υ: {exc}") from exc

        try:
            range_str = self.range_var.get().replace(",", ".").strip()
            if not range_str:
                raise ValueError("Το πεδίο range είναι κενό.")
            view_range = float(range_str)
        except ValueError as exc:
            raise ValueError(f"Άκυρο range: {exc}") from exc

        name = self.name_var.get().strip() or "Σημείο ΕΓΣΑ87"

        try:
            wgs = transform_egsa87_to_wgs84(x, y)
        except Exception as exc:
            raise ValueError(f"Αδυναμία μετατροπής συντεταγμένων: {exc}") from exc

        return PointModel(
            x=x,
            y=y,
            longitude=wgs.longitude,
            latitude=wgs.latitude,
            name=name,
            view_range=view_range,
        )

    def goto_point(self) -> None:
        try:
            point = self.parse_inputs()

            is_running = is_google_earth_running()
            is_saved = self._is_network_link_saved()

            if getattr(self, "has_opened_link", False):
                clear_delay = 3000
            elif not is_running:
                # Το ανοίγουμε αυτόματα
                self.open_network_link()
                self.has_opened_link = True
                # Δίνουμε 15 δευτερόλεπτα περιθώριο για να προλάβει να ανοίξει και να διαβάσει το fly-to
                clear_delay = 15000
            elif not is_saved:
                # Είναι ανοιχτό αλλά δεν έχει το link
                self.open_network_link()
                self.has_opened_link = True
                clear_delay = 5000
            else:
                self.has_opened_link = True
                clear_delay = 3000

            try:
                self.service.trigger_fly_to(point)
            except Exception as exc:
                raise RuntimeError(f"Αδυναμία εγγραφής KML (fly-to): {exc}") from exc

            # Καθαρίζουμε το αρχείο fly-to μετά τον απαραίτητο χρόνο
            self.after(clear_delay, self.clear_fly_to_silent)

            if is_running:
                self.after(3000, lambda: self.check_connection_status(point, attempt=1))

            self.status_var.set(
                f"Μετάβαση: ΕΓΣΑ87: X={point.x:.3f}, Y={point.y:.3f} | WGS84: lon={point.longitude:.8f}, lat={point.latitude:.8f}"
            )
        except Exception as exc:
            self.status_var.set(f"Σφάλμα: {str(exc)}")
            messagebox.showerror("Σφάλμα", str(exc))

    def check_connection_status(self, point, attempt: int = 1) -> None:
        import time

        last_poll = getattr(self.service, "last_poll_time", 0.0)
        if time.time() - last_poll > 4.0:
            if attempt == 1:
                # Auto-recovery: If the user deleted the link, startfile will bring it back.
                try:
                    self.service.update_all_kmls()
                    self.service.open_network_link_in_earth()
                    # Επαναφέρουμε το fly-to point γιατί πιθανώς το έσβησε ο timer (clear_fly_to_silent)
                    self.service.trigger_fly_to(point)
                    self.after(
                        5000, self.clear_fly_to_silent
                    )  # Ξανασβήνουμε μετά από λίγο
                    self.status_var.set(
                        "Προσπάθεια αυτόματης επανασύνδεσης με το Google Earth..."
                    )
                except Exception as e:
                    pass
                # Check again after 5 seconds to see if auto-recovery worked
                self.after(5000, lambda: self.check_connection_status(point, attempt=2))
            else:
                # Auto-recovery failed.
                msg = (
                    "Δεν υπάρχει ανταπόκριση από το Google Earth.\n"
                    "Η αυτόματη επανασύνδεση απέτυχε. Αυτό συμβαίνει αν το link έχει αποσυνδεθεί (κόκκινο εικονίδιο).\n\n"
                    "ΛΥΣΗ 1: Στο Google Earth, βρείτε το «ΕΓΣΑ87 Live Link», κάντε δεξί κλικ και «Ανανέωση».\n"
                    "ΛΥΣΗ 2: Κλείστε τελείως το Google Earth και πατήστε ξανά 'Μετάβαση' εδώ.\n\n"
                    "💡 Συμβουλή: Αν αποθηκεύσετε το «ΕΓΣΑ87 Live Link» στα 'Μέρη μου' του Google Earth, "
                    "η σύνδεση θα είναι πιο σταθερή!"
                )
                messagebox.showwarning("Απώλεια Σύνδεσης", msg)

    def clear_fly_to_silent(self) -> None:
        try:
            self.service.clear_fly_to()
        except Exception:
            pass

    def _is_network_link_saved(self) -> bool:
        try:
            myplaces_path = Path(
                os.path.expanduser(
                    r"~\AppData\LocalLow\Google\GoogleEarth\myplaces.kml"
                )
            )
            if myplaces_path.exists():
                content = myplaces_path.read_text(encoding="utf-8", errors="ignore")
                if (
                    "127.0.0.1:8000/live_link.kml" in content
                    or "127.0.0.1:8000/camera_update" in content
                ):
                    return True
        except:
            pass
        return False

    def open_network_link(self) -> None:
        if not is_google_earth_installed():
            self.prompt_google_earth_download()
            return

        try:
            is_saved = self._is_network_link_saved()

            if is_saved:
                if is_google_earth_running():
                    msg = (
                        "Το 'ΕΓΣΑ87 Live Link' φαίνεται να είναι ήδη αποθηκευμένο στα «Μέρη μου» του Google Earth!\n\n"
                        "Για να λειτουργήσει η εφαρμογή θα πρέπει :\n"
                        "- Είτε να διαγράψετε το 'ΕΓΣΑ87 Live Link' και να πατήσετε ξανά το Άνοιγμα\n"
                        "- Είτε να επιλέξετε με δεξί κλικ στο 'ΕΓΣΑ87 Live Link' «Ανανέωση»."
                    )
                    messagebox.showinfo("Ήδη αποθηκευμένο", msg)
                else:
                    self.service.update_all_kmls()
                    if launch_google_earth_empty():
                        self.status_var.set(
                            "Το Google Earth άνοιξε με το ήδη αποθηκευμένο link."
                        )
                    else:
                        # Fallback if launch fails
                        self.service.open_network_link_in_earth()
                        self.status_var.set(
                            "Άνοιξε το egsa87_live_link.kml στο Google Earth."
                        )
                self.has_opened_link = True
                return

            self.service.update_all_kmls()
            self.service.open_network_link_in_earth()
            self.has_opened_link = True
            self.status_var.set("Άνοιξε το egsa87_live_link.kml στο Google Earth.")
        except Exception as exc:
            self.status_var.set(f"Αδυναμία ανοίγματος αρχείου NetworkLink: {exc}")
            messagebox.showerror("Σφάλμα", f"Αδυναμία ανοίγματος αρχείου: {exc}")

    def prompt_google_earth_download(self) -> None:
        msg = "Το Google Earth δεν βρέθηκε στο σύστημά σας.\n\nΘέλετε να ανοίξετε τη σελίδα λήψης του Google Earth Pro;"
        res = messagebox.askyesno("Google Earth δεν βρέθηκε", msg)
        if res:
            webbrowser.open("https://www.google.com/earth/about/versions/#earth-pro")

    def open_google_maps(self) -> None:
        try:
            point = self.parse_inputs()
            url = f"https://www.google.com/maps/search/?api=1&query={point.latitude},{point.longitude}"
            webbrowser.open(url)
            self.status_var.set(
                f"Άνοιγμα Χαρτών Google: {point.latitude:.5f}, {point.longitude:.5f}"
            )
        except Exception as exc:
            self.status_var.set(f"Σφάλμα: {str(exc)}")
            messagebox.showerror("Σφάλμα", str(exc))

    def add_saved_point(self) -> None:
        try:
            point = self.parse_inputs()
            self.service.add_saved_point(point)
            self.status_var.set(
                f"Αποθηκεύτηκε: {point.name} (X={point.x:.3f}, Y={point.y:.3f})"
            )
        except Exception as exc:
            self.status_var.set(f"Αδυναμία αποθήκευσης σημείου/KML: {exc}")
            messagebox.showerror("Σφάλμα", str(exc))

    def copy_wgs84(self) -> None:
        try:
            point = self.parse_inputs()
            value = f"{point.latitude:.8f}, {point.longitude:.8f}"
            self.clipboard_clear()
            self.clipboard_append(value)
            self.status_var.set(f"Αντιγράφηκε στο πρόχειρο: {value}")
        except Exception as exc:
            self.status_var.set(f"Σφάλμα αντιγραφής: {exc}")
            messagebox.showerror("Σφάλμα", str(exc))

    def copy_target_xy(self) -> None:
        val = self.target_xy_var.get()
        if val and val not in ("-", "GE Εκτός σύνδεσης", "GE εκτός Ελλάδας"):
            self.clipboard_clear()
            self.clipboard_append(val)
            self.status_var.set(f"Αντιγράφηκε στο πρόχειρο: {val}")

    def open_work_dir(self) -> None:
        try:
            self.service.open_working_directory()
            self.status_var.set("Άνοιγμα προσωρινού φακέλου εργασίας")
        except Exception as exc:
            self.status_var.set(f"Αδυναμία ανοίγματος φακέλου: {exc}")
            messagebox.showerror("Σφάλμα", str(exc))
