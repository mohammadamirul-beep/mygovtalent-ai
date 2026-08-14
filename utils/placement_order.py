from io import BytesIO
from datetime import datetime

from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors


def _v(row, key, default=""):
    if row is None:
        return default
    try:
        value = row[key]
    except (KeyError, IndexError, TypeError):
        try:
            value = row.get(key, default)
        except AttributeError:
            value = default
    return default if value is None else str(value)


def _p(text, style):
    return Paragraph(str(text or "").replace("\n", "<br/>"), style)


def generate_placement_order_pdf(
    placement,
    profile=None,
    vacancy=None,
    reference_no=None,
    effective_date=None,
    recipient_address=None,
    copy_to_address=None,
    signed_by=None,
    signed_at=None,
):
    """
    Generate a DEMO/DRAFT placement-order PDF following the structure
    of the uploaded KPM sample.

    This is a draft generator for the MyGovTalent AI prototype.
    It does not reproduce a real signature/seal and must not be treated
    as an official government document until authorised and digitally signed.
    """

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=18 * mm,
        title="Draf Arahan Penempatan Pegawai Perkhidmatan Pendidikan",
        author="MyGovTalent AI",
    )

    styles = getSampleStyleSheet()

    header = ParagraphStyle(
        "Header",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        alignment=TA_LEFT,
        spaceAfter=1,
    )

    header_en = ParagraphStyle(
        "HeaderEn",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=11,
        alignment=TA_LEFT,
    )

    small = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
    )

    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        alignment=TA_LEFT,
        spaceAfter=7,
    )

    body_indent = ParagraphStyle(
        "BodyIndent",
        parent=body,
        leftIndent=12 * mm,
        firstLineIndent=0,
    )

    title = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        alignment=TA_CENTER,
        spaceBefore=8,
        spaceAfter=8,
    )

    right = ParagraphStyle(
        "Right",
        parent=small,
        alignment=TA_RIGHT,
    )

    sign = ParagraphStyle(
        "Sign",
        parent=body,
        leading=13,
    )

    name = _v(profile, "name", _v(placement, "name", "NAMA PEGAWAI"))
    ic = _v(profile, "ic", "________________")
    current_position = _v(
        profile, "current_position", _v(placement, "current_position", "Jawatan Semasa")
    )
    grade = _v(profile, "grade", _v(placement, "grade", ""))
    current_department = _v(
        profile,
        "current_department",
        _v(placement, "department", "Bahagian Asal"),
    )

    new_position = _v(
        vacancy,
        "title",
        _v(placement, "title", "Jawatan Penempatan"),
    )
    new_department = _v(
        vacancy,
        "department",
        _v(placement, "target_department", "Bahagian Baharu"),
    )

    # Vacancy does not currently have a "substantive grade" field in the
    # prototype schema, so use the vacancy grade if one is later added.
    position_grade = _v(vacancy, "grade", grade or "________")
    substantive_grade = _v(
        vacancy,
        "substantive_grade",
        "________",
    )

    if not effective_date:
        effective_date = _v(
            placement,
            "placement_date",
            datetime.now().strftime("%d %B %Y"),
        )

    if not reference_no:
        reference_no = f"MYGT/BPSM/{_v(placement, 'id', 'DRAFT')}"

    recipient_address = recipient_address or [
        current_department,
        "Kementerian Pendidikan Malaysia",
        "62604 PUTRAJAYA",
    ]

    copy_to_address = copy_to_address or [
        new_department,
        "Kementerian Pendidikan Malaysia",
        "62604 PUTRAJAYA",
    ]

    story = []

    # Header block — mirrors the hierarchy in the sample.
    header_data = [
        [
            _p("KEMENTERIAN PENDIDIKAN MALAYSIA", header),
            _p(
                f"Ruj. Kami : {reference_no}<br/>"
                f"Tarikh&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: {datetime.now().strftime('%d %B %Y')}",
                small,
            ),
        ],
        [
            _p("MINISTRY OF EDUCATION MALAYSIA", header_en),
            "",
        ],
        [
            _p("BAHAGIAN PENGURUSAN SUMBER MANUSIA", header),
            "",
        ],
    ]

    header_table = Table(
        header_data,
        colWidths=[105 * mm, 60 * mm],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, -1), (-1, -1), 0.7, colors.black),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 7 * mm))

    story.append(_p(f"<b>{name.upper()}</b>", body))
    story.append(_p(f"<b>NO. KAD PENGENALAN: {ic}</b>", body))

    story.append(_p("<b>Melalui dan Salinan:</b>", body))
    for line in recipient_address:
        story.append(_p(line, body))
    story.append(Spacer(1, 2 * mm))

    story.append(_p("Tuan,", body))
    story.append(_p("ARAHAN PENEMPATAN PEGAWAI PERKHIDMATAN PENDIDIKAN", title))

    para1 = (
        f"Dimaklumkan bahawa <b>{name}</b>, Pegawai Perkhidmatan Pendidikan (PPP) "
        f"Gred <b>{grade or position_grade}</b>, {current_position}, "
        f"{current_department} ditempatkan sebagai <b>{new_position}</b>, "
        f"{new_department}, PPP Gred <b>{position_grade}</b>. "
        f"Gred hakiki jawatan ialah <b>{substantive_grade}</b>."
    )
    story.append(_p(para1, body_indent))

    story.append(
        _p(
            f"<b>2.</b>&nbsp;&nbsp;Tarikh berkuat kuasa penempatan ini ialah mulai "
            f"<b>{effective_date}</b>.",
            body,
        )
    )

    story.append(
        _p(
            "<b>3.</b>&nbsp;&nbsp;Kegagalan tuan mematuhi arahan penempatan ini "
            "boleh menyebabkan tuan dikenakan tindakan tatatertib berdasarkan "
            "peraturan yang berkuat kuasa.",
            body,
        )
    )

    story.append(
        _p(
            "<b>4.</b>&nbsp;&nbsp;Ketua Jabatan dikehendaki menyediakan Penyata "
            "Perubahan (Kew.8), mengemukakan Sijil Gaji Akhir dan Buku Perkhidmatan "
            "Kerajaan kepada Ketua Jabatan yang baharu serta meminta pegawai "
            "berkenaan menyediakan Nota Serah Tugas (jika berkaitan). "
            "Ketua Jabatan yang berkenaan juga dikehendaki mengemas kini data "
            "pegawai dalam sistem yang berkaitan dalam tempoh yang ditetapkan.",
            body,
        )
    )

    story.append(_p("Sekian, terima kasih.", body))
    story.append(_p("<b>\"MALAYSIA MADANI\"</b>", body))
    story.append(_p("<b>\"BERKHIDMAT UNTUK NEGARA\"</b>", body))
    story.append(_p("Saya yang menjalankan amanah", sign))
    story.append(Spacer(1, 9 * mm))

    if signed_by:
        story.append(
            _p(
                "<b>DITANDATANGANI SECARA DIGITAL</b><br/>"
                f"Nama: <b>{signed_by}</b><br/>"
                "Jawatan: Ketua Pengarah / KPPM<br/>"
                f"Tarikh/Masa: {signed_at or '-'}",
                sign,
            )
        )
        story.append(
            _p(
                "<b>STATUS: ARAHAN PENEMPATAN DILULUSKAN KPPM</b>",
                sign,
            )
        )
    else:
        story.append(_p("<b>[ RUANG TANDATANGAN DIGITAL KPPM ]</b>", sign))
        story.append(_p("Ketua Pengarah / KPPM", sign))

    story.append(Spacer(1, 6 * mm))
    story.append(
        _p(
            (
                "<b>ARAHAN PENEMPATAN RASMI — DILULUSKAN KPPM</b><br/>"
                "Dokumen ini telah ditandatangani secara digital oleh KPPM."
                if signed_by
                else
                "<b>DRAF — UNTUK SEMAKAN BPSM / KPPM</b><br/>"
                "Dokumen ini dijana oleh MyGovTalent AI sebagai draf. "
                "Ia bukan arahan penempatan rasmi sehingga diluluskan dan "
                "ditandatangani oleh pihak berkuasa yang berkenaan."
            ),
            small,
        )
    )

    # Copy recipient section on the same page, matching the sample's
    # "Melalui dan Salinan" concept.
    story.append(Spacer(1, 4 * mm))
    story.append(_p("<b>Salinan:</b>", small))
    for line in copy_to_address:
        story.append(_p(line, small))

    doc.build(story)

    buffer.seek(0)
    return buffer.getvalue()