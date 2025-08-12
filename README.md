# 🎫 SAMFUNDET BILLETT BOT

Automated ticket purchasing for Samfundet events. Gets you to the payment page fast during high-demand sales.

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install selenium webdriver-manager
   ```

2. **Set your event details in `main.py`:**
   ```python
   open_event_when_live(
       url="https://www.samfundet.no/arrangement/4596-toga-hele-huset",
       onsale_iso="2025-08-12T13:59:58+02:00",  # 2 seconds before sale time
       chrome_profile_dir=None
   )
   ```

3. **Run it:**
   ```bash
   python main.py
   ```

## ⏰ Timing

Start **2-5 seconds before** the official sale time:
- For 14:00 sale: `"2025-08-12T13:59:58+02:00"`
- For 12:00 sale: `"2025-08-12T11:59:58+02:00"`

## � What It Does

1. Opens event page at sale time
2. Hunts for "Kjøp billett" button (30 seconds)
3. Selects 4 Medlem + 9 Ikke-medlem tickets
4. Fills your email: `jakobildstad@gmail.com`
5. Clicks "Til betaling"
6. **You complete the payment manually**

## 🎪 Supported Events

Works for any Samfundet event:
- Silent Disco: `4572-silent-disco`
- Toga Party: `4596-toga-hele-huset`
- Any other event

## ✅ Success Signs

Watch for these logs:
- `✅ SUCCESS! Clicked buy button`
- `✅ Selected 4 tickets for Medlem`
- `✅ Selected 9 tickets for Ikke-medlem`
- `✅ SUCCESS! Clicked 'Til betaling' button`

## � Customization

**Change email:** Edit `jakobildstad@gmail.com` in the script
**Change tickets:** Modify `select_by_value("4")` and `select_by_value("9")`

---

**Use responsibly. Complete payment manually for security.**
