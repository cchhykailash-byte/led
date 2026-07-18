"""
.com.np Cover Letter Generator
--------------------------------
A Streamlit web app that takes applicant details from a form and
automatically generates a professional cover letter (for requesting a
.com.np domain registration) rendered as a downloadable JPEG image.

Run with:
    streamlit run comnp_cover_letter_app.py

Dependencies:
    pip install streamlit pillow
"""

import io
import textwrap
from datetime import date

import streamlit as st
from PIL import Image, ImageDraw, ImageFont


# ----------------------------------------------------------------------
# Page configuration
# ----------------------------------------------------------------------
st.set_page_config(
    page_title=".com.np Cover Letter Generator",
    page_icon="📄",
    layout="centered",
)


# ----------------------------------------------------------------------
# Font helpers
# ----------------------------------------------------------------------
# Several candidate paths are listed for each style, covering common
# Linux, macOS, and Windows installs, plus bare font names that work if
# the OS's font-config can resolve them by name. The first one that
# loads successfully on the machine running this app is used.
FONT_CANDIDATES_SERIF = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",           # Linux
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "/Library/Fonts/Georgia.ttf",                                  # macOS
    "/System/Library/Fonts/Supplemental/Georgia.ttf",              # macOS
    "C:\\Windows\\Fonts\\georgia.ttf",                              # Windows
    "C:\\Windows\\Fonts\\times.ttf",                                # Windows
    "DejaVuSerif.ttf",
]
FONT_CANDIDATES_SERIF_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",       # Linux
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "/Library/Fonts/Georgia Bold.ttf",                             # macOS
    "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",         # macOS
    "C:\\Windows\\Fonts\\georgiab.ttf",                             # Windows
    "C:\\Windows\\Fonts\\timesbd.ttf",                              # Windows
    "DejaVuSerif-Bold.ttf",
]


@st.cache_resource(show_spinner=False)
def load_font(bold: bool, size: int) -> ImageFont.FreeTypeFont:
    """Load a serif font (regular or bold) at the given size.

    Tries several common cross-platform font paths first. If a bold
    font truly can't be found anywhere, it falls back to the regular
    serif font at the SAME size (so text stays the correct, consistent
    size even if it isn't visually bold) rather than silently dropping
    to PIL's tiny built-in bitmap font, which is what caused the
    Subject line and signature name to look mismatched and undersized.
    """
    paths = FONT_CANDIDATES_SERIF_BOLD if bold else FONT_CANDIDATES_SERIF
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue

    if bold:
        # Bold not found anywhere -- reuse the regular serif font so the
        # size/family still matches the rest of the letter.
        for path in FONT_CANDIDATES_SERIF:
            try:
                return ImageFont.truetype(path, size)
            except (OSError, IOError):
                continue

    # Absolute last resort: PIL's built-in font, scaled as close as
    # possible to the requested size so spacing still stays consistent.
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        # Older Pillow versions don't support the size argument.
        return ImageFont.load_default()


# ----------------------------------------------------------------------
# Letter generation
# ----------------------------------------------------------------------
PAGE_WIDTH = 1240   # ~ A4 at 150dpi
PAGE_HEIGHT = 1754
MARGIN_X = 120
MARGIN_TOP = 110

TEXT_COLOR = (25, 25, 25)
BG_COLOR = (255, 255, 255)

WRAP_WIDTH = 78  # characters per line for body paragraphs
SUBJECT_WRAP_WIDTH = 52  # subject line is bigger, so wrap sooner


def build_letter_image(data: dict) -> Image.Image:
    """Render the cover letter onto a JPEG-ready PIL Image using the
    supplied applicant data dictionary."""

    img = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    font_body = load_font(bold=False, size=26)
    font_bold = load_font(bold=True, size=26)
    font_subject = load_font(bold=True, size=34)   # clearly larger than body text
    font_small = load_font(bold=False, size=22)

    x = MARGIN_X
    y = MARGIN_TOP
    line_gap = 14

    def line_height(font):
        bbox = font.getbbox("Ag")
        return (bbox[3] - bbox[1]) + line_gap

    def write_line(text, font=font_body, extra_gap=0):
        nonlocal y
        draw.text((x, y), text, font=font, fill=TEXT_COLOR)
        y += line_height(font) + extra_gap

    def write_wrapped(text, font=font_body, width=WRAP_WIDTH, extra_gap=6):
        nonlocal y
        if not text:
            return
        for wline in textwrap.wrap(text, width=width):
            draw.text((x, y), wline, font=font, fill=TEXT_COLOR)
            y += line_height(font)
        y += extra_gap

    # ---- Date (top left) ----
    date_str = data["today"].strftime("%B %d, %Y")
    draw.text((x, y), date_str, font=font_small, fill=TEXT_COLOR)
    y += line_height(font_small) + 30

    # ---- Recipient block ----
    write_line("To,", font_body)
    write_line("The Hostmaster", font_body)
    write_line("Mercantile Communications Pvt. Ltd.", font_body)
    write_line("Kathmandu, Nepal", font_body, extra_gap=30)

    # ---- Subject (larger, normal-looking heading size) ----
    write_wrapped(
        f'Subject: Request for Registration of "{data["domain"]}" Domain',
        font=font_subject,
        width=SUBJECT_WRAP_WIDTH,
        extra_gap=30,
    )

    # ---- Salutation ----
    write_line("Respected Sir/Madam,", font_body, extra_gap=20)

    # ---- Opening paragraph ----
    write_wrapped(
        f'I, {data["name"]}, respectfully request the registration of the '
        f'domain "{data["domain"]}" for the purposes described below. '
        f"My details are as follows:",
        extra_gap=24,
    )

    # ---- Details block ----
    def write_field(label, value):
        if not value:
            return
        write_line(f"{label}: {value}", font_body)

    write_field("Name", data["name"])
    write_field("Permanent Address", data["permanent_address"])
    write_field("Current Address", data["current_address"])
    write_field("Citizenship No.", data["citizenship"])
    write_field("Email", data["email"])
    write_field("Phone", data["phone"])
    if data["organization"]:
        write_field("Organization", data["organization"])
    y += 20

    # ---- Purpose paragraph ----
    write_wrapped(
        f'The requested domain "{data["domain"]}" will be used for '
        f'{data["purpose"]}.',
        extra_gap=24,
    )

    write_wrapped(
        "I kindly request you to review and approve my application at your "
        "earliest convenience.",
        extra_gap=24,
    )

    write_line("Thank you.", font_body, extra_gap=40)

    # ---- Closing (no signature line) ----
    write_line("Sincerely,", font_body, extra_gap=25)
    write_line(data["name"], font_bold)

    return img


# ----------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------
REQUIRED_FIELDS = [
    ("name", "Full Name"),
    ("permanent_address", "Permanent Address"),
    ("email", "Email"),
    ("phone", "Phone Number"),
    ("domain", "Requested Domain"),
    ("purpose", "Purpose"),
]


def validate(values: dict):
    missing = [label for key, label in REQUIRED_FIELDS if not values.get(key, "").strip()]
    return missing


# ----------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------
st.title("📄 .com.np Cover Letter Generator")
st.caption("Fill in your details below to automatically generate a professional "
           "cover letter for .com.np domain registration.")

if "letter_image_bytes" not in st.session_state:
    st.session_state.letter_image_bytes = None

with st.form("cover_letter_form", clear_on_submit=False):
    st.subheader("Enter Details")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name *", placeholder="e.g. Kailash Chaudhary")
        citizenship = st.text_input("Citizenship Number")
        email = st.text_input("Email *", placeholder="you@example.com")
    with col2:
        permanent_address = st.text_input("Permanent Address *", placeholder="City, District, Province")
        current_address = st.text_input("Current Address")
        phone = st.text_input("Phone Number *", placeholder="98XXXXXXXX")

    organization = st.text_input("Organization (optional)")
    domain = st.text_input("Requested Domain *", placeholder="example.com.np")
    purpose = st.text_area(
        "Purpose of Domain *",
        placeholder="e.g. educational, professional and personal portfolio purposes",
        height=90,
    )

    submitted = st.form_submit_button("Generate Letter", use_container_width=True)

values = {
    "name": name,
    "permanent_address": permanent_address,
    "current_address": current_address,
    "citizenship": citizenship,
    "email": email,
    "phone": phone,
    "organization": organization,
    "domain": domain,
    "purpose": purpose,
}

def compress_to_target_size(img: Image.Image, target_kb: int = 150) -> bytes:
    """Save `img` as JPEG, stepping quality (and, if needed, resolution)
    down until the output is under target_kb kilobytes. Returns the final
    JPEG bytes. Always returns something, even if it can't quite hit the
    target (uses the smallest attempt made)."""
    target_bytes = target_kb * 1024
    best_bytes = None

    working_img = img
    # Try progressively lower quality first -- this preserves full
    # resolution/sharpness of the text as long as possible.
    for quality in (90, 85, 80, 75, 70, 65, 60, 50, 40):
        buf = io.BytesIO()
        working_img.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
        data = buf.getvalue()
        if best_bytes is None or len(data) < len(best_bytes):
            best_bytes = data
        if len(data) <= target_bytes:
            return data

    # Still too big -- scale the image down and retry at a modest quality.
    for scale in (0.85, 0.7, 0.55):
        w, h = int(img.width * scale), int(img.height * scale)
        resized = img.resize((w, h), Image.LANCZOS)
        for quality in (80, 65, 50):
            buf = io.BytesIO()
            resized.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
            data = buf.getvalue()
            if best_bytes is None or len(data) < len(best_bytes):
                best_bytes = data
            if len(data) <= target_bytes:
                return data

    # Couldn't hit the target -- return the smallest version produced.
    return best_bytes


if submitted:
    missing = validate(values)
    if missing:
        st.error("⚠️ Please complete all required fields: " + ", ".join(missing))
        st.session_state.letter_image_bytes = None
    else:
        data = dict(values)
        data["today"] = date.today()
        letter_img = build_letter_image(data)

        st.session_state.letter_image_bytes = compress_to_target_size(letter_img, target_kb=140)
        st.success("✅ Letter generated successfully!")

# ----------------------------------------------------------------------
# Preview + Download
# ----------------------------------------------------------------------
st.subheader("Preview")

if st.session_state.letter_image_bytes:
    st.image(st.session_state.letter_image_bytes, use_container_width=True)
    st.download_button(
        label="⬇️ Download JPG",
        data=st.session_state.letter_image_bytes,
        file_name=f"{(name or 'cover_letter').strip().replace(' ', '_')}_domain_cover_letter.jpg",
        mime="image/jpeg",
        use_container_width=True,
    )
else:
    st.info("Fill in the required fields above and click **Generate Letter** to see a preview here.")
    st.button("⬇️ Download JPG", disabled=True, use_container_width=True)
