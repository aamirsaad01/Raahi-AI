"""

Interactive terminal chat with OpenAI (Raahi persona).



Run from repo root or from backend_scripts:

  python backend_scripts/test_chatbot.py

  cd backend_scripts && python test_chatbot.py



Requires: pip install openai

"""



import os

import sys



import psycopg2

from dotenv import load_dotenv



system_prompt = (

    "You are Raahi, an expert, empathetic local travel guide for Pakistan. The current year is 2026. "

    "You must NEVER mention COVID-19, masks, or pandemic precautions under any circumstances. "

    "Your primary goal is current user safety and providing cultural tips. CRITICAL INSTRUCTION: "

    "You must dynamically match the language of the user. If the user asks a question in English, "

    "you must reply entirely in English. If the user asks a question in Roman Urdu or Urdu, you must "

    "reply fluidly in Roman Urdu."

)



repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env_path = os.path.join(repo_root, ".env")

load_dotenv(dotenv_path=env_path)





def get_active_hazards() -> str:

    """

    Load recent active hazards from PostgreSQL (NDMA AI alerts + user reports).

    Returns a formatted string for system context, or "" if DB is unavailable or empty.

    """

    try:

        conn = psycopg2.connect(

            dbname=os.getenv("DB_NAME", "raahi_ai"),

            user=os.getenv("DB_USER", "postgres"),

            password=os.getenv("DB_PASSWORD", ""),

            host=os.getenv("DB_HOST", "127.0.0.1"),

            port=os.getenv("DB_PORT", "5432"),

        )

        cur = conn.cursor()

        lines: list[str] = []



        cur.execute(

            """

            SELECT EXISTS (

                SELECT FROM information_schema.tables

                WHERE table_schema = 'public' AND table_name = 'ndma_alerts_ai'

            )

            """

        )

        if cur.fetchone()[0]:

            cur.execute(

                """

                SELECT 1 FROM information_schema.columns

                WHERE table_name = 'ndma_alerts_ai' AND column_name = 'is_active'

                LIMIT 1

                """

            )

            has_is_active = cur.fetchone() is not None

            if has_is_active:

                ndma_sql = """

                    SELECT location_name, heading, COALESCE(description, ''), severity,

                           COALESCE(icon_type, ''), scraped_at

                    FROM ndma_alerts_ai

                    WHERE (is_active = TRUE OR is_active IS NULL)

                    ORDER BY scraped_at DESC NULLS LAST

                    LIMIT %s

                """

            else:

                ndma_sql = """

                    SELECT location_name, heading, COALESCE(description, ''), severity,

                           COALESCE(icon_type, ''), scraped_at

                    FROM ndma_alerts_ai

                    ORDER BY scraped_at DESC NULLS LAST

                    LIMIT %s

                """

            cur.execute(ndma_sql, (15,))

            for row in cur.fetchall():

                loc, heading, desc, severity, icon_type, _scraped = row

                detail = (heading or "").strip()

                if desc and str(desc).strip():

                    detail = f"{detail}: {desc}".strip(": ") if detail else str(desc).strip()

                if not detail:

                    detail = "No description"

                lines.append(

                    f"- Location: {loc} | Source: NDMA | Type: {icon_type or 'unknown'} | "

                    f"Severity: {severity} | Alert: {detail}"

                )



        cur.execute(

            """

            SELECT EXISTS (

                SELECT FROM information_schema.tables

                WHERE table_schema = 'public' AND table_name = 'hazard_reports'

            )

            """

        )

        if cur.fetchone()[0]:

            cur.execute(

                """

                SELECT 1 FROM information_schema.columns

                WHERE table_name = 'hazard_reports' AND column_name = 'hazard_type'

                LIMIT 1

                """

            )

            has_hazard_type = cur.fetchone() is not None

            if has_hazard_type:

                user_sql = """

                    SELECT location, title, COALESCE(description, ''), severity, COALESCE(hazard_type, '')

                    FROM hazard_reports

                    ORDER BY reported_at DESC NULLS LAST

                    LIMIT %s

                """

            else:

                user_sql = """

                    SELECT location, title, COALESCE(description, ''), severity

                    FROM hazard_reports

                    ORDER BY reported_at DESC NULLS LAST

                    LIMIT %s

                """

            cur.execute(user_sql, (10,))

            rows = cur.fetchall()

            for row in rows:

                if has_hazard_type:

                    loc, title, desc, severity, hazard_type = row

                    type_part = hazard_type or "unknown"

                else:

                    loc, title, desc, severity = row

                    type_part = "unknown"

                detail = (title or "").strip()

                if desc and str(desc).strip():

                    detail = f"{detail}: {desc}".strip(": ") if detail else str(desc).strip()

                if not detail:

                    detail = "No description"

                loc_str = (loc or "Unknown").strip()

                lines.append(

                    f"- Location: {loc_str} | Source: Crowd-sourced | Type: {type_part} | "

                    f"Severity: {severity} | Alert: {detail}"

                )



        cur.close()

        conn.close()



        if not lines:

            return ""

        return "Real-Time Hazards:\n" + "\n".join(lines)

    except Exception:

        return ""





def main() -> int:

    try:

        from openai import OpenAI

    except ImportError:

        print("Missing package: openai")

        print("Install with: pip install openai")

        return 1



    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not api_key:

        print("OPENAI_API_KEY is not set.")

        print(f"Add it to {env_path} (or export it in your shell).")

        return 1



    client = OpenAI(api_key=api_key)

    model = "gpt-4o-mini"



    hazards_string = get_active_hazards()

    conversation_history = [

        {"role": "system", "content": f"{system_prompt}\n\n{hazards_string}"}

    ]



    print("=" * 60)

    print("Raahi (terminal chat) — type 'exit' to quit")

    print("=" * 60)



    while True:

        user_text = input("You: ")

        if user_text.strip() == "exit":

            break



        conversation_history.append({"role": "user", "content": user_text})



        try:

            response = client.chat.completions.create(

                model=model,

                messages=conversation_history,

            )

        except Exception as e:

            print(f"Request failed: {e}")

            conversation_history.pop()

            continue



        assistant_text = (response.choices[0].message.content or "").strip()

        print(f"Raahi: {assistant_text}\n")



        conversation_history.append(

            {"role": "assistant", "content": assistant_text}

        )



    print("Goodbye.")

    return 0





if __name__ == "__main__":

    sys.exit(main())

