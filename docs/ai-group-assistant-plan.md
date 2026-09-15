# Plan defensywnego asystenta grupowego AI (Telegram/Telethon)

> Dokument dotyczy wyłącznie jawnego, audytowalnego asystenta do obsługi alertów,
> triage i runbooków obronnych. Nie definiuje kanału sterowania narzędziami
> ofensywnymi i nie rozszerza funkcjonalności repozytorium.

## Zasady projektowe

- Asystent jest **read-mostly**: odbiera zgłoszenia, porządkuje je, odsyła link do
  runbooka i proponuje działania. Nie wykonuje samodzielnie zmian w infrastrukturze.
- Każda wiadomość zawiera oznaczenie, że jest generowana przez AI, identyfikator
  sprawy i odnośnik do audytu. Historia decyzji jest niemodyfikowalna dla zwykłego
  operatora.
- Decyzja wysokiego ryzyka wymaga **human-in-the-loop**: potwierdzenia dwóch
  uprawnionych osób albo jawnej akceptacji właściciela usługi. Brak odpowiedzi,
  niejednoznaczność lub błąd walidacji oznacza odmowę, nie automatyczne ponowienie.
- Model otrzymuje minimalny, zredagowany kontekst. Dane grupy, tokeny, dane osobowe
  i sekrety nie są wysyłane do modelu bez osobnej, zatwierdzonej podstawy.

## Tożsamość Telegram i Telethon

1. Używana jest dedykowana tożsamość bota lub konta serwisowego, bez uprawnień
   administratora grupy, jeśli nie są bezwzględnie wymagane.
2. Sesja Telethon jest przechowywana jako sekret dostarczany po attestation;
   plik sesji nie trafia do repozytorium, obrazu ani logów. Tokeny mają rotację,
   unieważnienie i właściciela.
3. Lista dozwolonych grup, tematów i identyfikatorów operatorów jest jawna,
   wersjonowana i sprawdzana przed każdym działaniem. Wiadomości spoza allowlisty
   są odrzucane i logowane bez przetwarzania przez model.
4. Uprawnienia Telegrama ograniczają się do odczytu zgłoszeń i publikowania
   odpowiedzi w przeznaczonym wątku. Dodawanie użytkowników, zmiana uprawnień,
   usuwanie historii, wysyłanie plików i wywoływanie niezatwierdzonych botów są
   wyłączone.
5. Połączenie wychodzące jest ograniczone do wymaganych endpointów Telegrama,
   dostawcy modelu i centralnego logowania. Telethon nie nasłuchuje portów
   przychodzących i nie udostępnia powłoki.

## Przepływ wiadomości i kontrola poleceń

1. Odbiornik zapisuje metadane (grupa, autor, czas, identyfikator wiadomości) oraz
   stosuje limit częstotliwości, limit rozmiaru i ochronę przed replay.
2. Parser rozdziela tekst od załączników, redaguje sekrety i klasyfikuje żądanie:
   informacja, alert, prośba o zmianę lub treść nieobsługiwana. Prompt injection,
   instrukcje ukryte w załącznikach i próby zmiany polityki są traktowane jako dane,
   nigdy jako autoryzacja.
3. Asystent może zaproponować bezpieczny runbook, ale nie może wykonywać poleceń
   systemowych, arbitralnego kodu, skryptów, połączeń z hostami ani operacji
   wymagających eskalacji. Ewentualna integracja z zatwierdzonym systemem biletowym
   odbywa się przez stałe, parametryzowane akcje z walidacją schematu.
4. Przed publikacją odpowiedź przechodzi kontrolę PII/sekretów, limit długości i
   filtr treści. Działania zmieniające stan wymagają wyświetlenia planu, zakresu,
   przewidywanego wpływu, osoby zatwierdzającej i przycisku „Anuluj”.
5. Każde odrzucenie, timeout, ponowienie i ręczne zatwierdzenie jest audytowane.
   Idempotency key zapobiega podwójnemu wykonaniu tej samej zatwierdzonej akcji.

## Minimalny model uprawnień

Role są rozdzielone: obserwator może czytać status, analityk może tworzyć sprawy,
a approver może zatwierdzić wcześniej zdefiniowany runbook. Nikt przez Telegram nie
otrzymuje dostępu do powłoki, sekretów, kluczy hosta ani funkcji administracyjnych
Telegrama. Uprawnienia są krótkotrwałe, okresowo przeglądane i natychmiast
unieważniane po zmianie zespołu lub incydencie.

## Audyt, prywatność i operacje

Centralny audyt przechowuje identyfikatory, decyzje, wersję promptu/polityki, wynik
walidacji, approvera i czas UTC. Przechowuje minimalny wycinek treści potrzebny do
odtworzenia decyzji; sekrety i pełne załączniki są redagowane lub zastępowane
identyfikatorem retencji. Dostęp do audytu jest rozdzielony od dostępu operatora.

Monitoring obejmuje opóźnienie, błędy Telethon, odrzucenia allowlisty, nietypowy
wzrost wiadomości, brak logów i zmianę fingerprintu sesji. Alarm powoduje
read-only mode oraz odcięcie sesji, a nie próbę „samodzielnego naprawienia”.
Procedura IR obejmuje rotację tokenu Telegram, unieważnienie sesji Telethon,
odcięcie dostawcy modelu, zabezpieczenie logów i ręczne wznowienie po przeglądzie.

## Kryteria wdrożenia i testy

- test pozytywny: dozwolona wiadomość tworzy sprawę z pełnym audytem;
- test negatywny: nieznana grupa, nieznany operator, replay i prompt injection są
  odrzucane bez wykonania akcji;
- test uprawnień: konto serwisowe nie może zmieniać członkostwa, czytać sekretów
  ani uruchamiać poleceń;
- test awarii: brak Telegrama, modelu, czasu lub centralnego logowania kończy się
  bezpiecznym zatrzymaniem i widocznym alertem;
- test IR/recovery: token i sesję można unieważnić, odtworzyć konfigurację z kopii
  oraz potwierdzić, że wznowienie wymaga człowieka.

## Jawne wykluczenia

Asystent nie jest C2 i nie służy do evasion, ukrytej persistence, reverse shell,
port knocking, eksfiltracji, „Shadow Agent” ani self-erasure. Nie implementuje
ukrytych poleceń, automatycznego obchodzenia zgód, kasowania śladów ani funkcji
zwiększających zasięg lub skuteczność ataku. W razie konfliktu między wygodą a
audytowalnością obowiązuje audytowalność i ręczne zatrzymanie.
