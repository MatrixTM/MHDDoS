# Blueprint: defensywny, efemeryczny system operacyjny

> **Zakres i zastrzeżenie:** Ten dokument opisuje wyłącznie zabezpieczenia infrastruktury,
> rozliczalność i reagowanie na incydenty. Nie jest instrukcją uruchamiania, ukrywania ani
> rozszerzania funkcji ofensywnych. W kontekście repozytorium o charakterze ofensywnym
> wszystkie opisane mechanizmy mają służyć ochronie administratora, ograniczeniu
> uprawnień i szybkiemu zatrzymaniu systemu.

## Cele i granice zaufania

System powinien uruchamiać się z możliwie małego, niezmiennego obrazu, wykonywać pracę
w pamięci, a po zakończeniu usuwać stan roboczy. Trwałe dane ograniczają się do
zweryfikowanego obrazu, konfiguracji zarządzanej poza hostem oraz szyfrowanych logów
audytowych. Każda zmiana obrazu, polityki lub tożsamości operatora musi być możliwa do
odtworzenia z logów.

Model zagrożeń obejmuje: zmodyfikowany obraz lub bootloader, przejęte konto operatora,
kradzież tokenu, złośliwe polecenie z kanału komunikacyjnego, eskalację uprawnień,
wyciek danych z pamięci i utratę hosta. Kanał administracyjny, host wykonawczy i
centralny system logowania są odrębnymi domenami zaufania.

## Łańcuch rozruchowy i integralność

1. **Secure Boot** powinien akceptować wyłącznie podpisany bootloader, kernel i initramfs.
   Klucze właściciela platformy są przechowywane i rotowane zgodnie z procedurą
   zarządzania kluczami; tryb awaryjny nie może po cichu obniżać wymagań.
2. **Measured boot** zapisuje pomiary kolejnych etapów do TPM PCR. Sam pomiar nie
   blokuje uruchomienia, dlatego wynik musi być porównywany z zatwierdzonym profilem
   przed dopuszczeniem hosta do pracy.
3. **TPM attestation** dostarcza zdalnemu punktowi kontrolnemu dowód, że host uruchomił
   zatwierdzony obraz i politykę. Attestation jest krótkotrwała, powiązana z nonce oraz
   tożsamością hosta; odrzucenie dowodu oznacza brak dostępu do sekretów i ruchu
   administracyjnego.
4. Obraz jest budowany powtarzalnie, podpisywany poza hostem i publikowany z sumą
   kontrolną. Host pobiera tylko wersję dopuszczoną przez politykę, a aktualizacja ma
   ścieżkę powrotu do ostatniego znanego dobrego obrazu.
5. Przy starcie wykonywana jest kontrola integralności plików systemowych i polityk.
   Wyniki, wersja obrazu, PCR i identyfikator attestation trafiają do centralnego
   dziennika przed udostępnieniem usługi.

## Efemeryczność, RAM i tmpfs

- System plików roboczych jest montowany jako **RAM/tmpfs** z limitami rozmiaru,
  `nodev`, `nosuid` i `noexec` wszędzie, gdzie nie jest wymagane wykonywanie.
- Sekrety są dostarczane po pomyślnej attestation, przechowywane tylko tak długo, jak
  wymaga tego zadanie, a następnie zerowane i unieważniane po stronie dostawcy.
- Swap, hibernacja, zrzuty pamięci i automatyczne core dumpy są wyłączone albo
  szyfrowane i objęte kontrolą dostępu. Diagnostyka wrażliwa wymaga jawnej zgody
  i rejestracji.
- Dane wejściowe są walidowane, ograniczane rozmiarem i przechowywane w odseparowanym
  katalogu tymczasowym. Po zatrzymaniu usługi tmpfs jest odmontowany, a uchwyty plików
  zamykane; trwałe nośniki nie są używane jako ukryty magazyn.
- Reboot lub utrata attestation powoduje bezpieczne zatrzymanie i unieważnienie sesji,
  nie zaś próbę odzyskiwania działania w tle.

## Tożsamość i SSH hardening

- Dostęp SSH jest dozwolony wyłącznie z zarządzanej sieci administracyjnej przez
  bastion, z kluczami sprzętowymi lub innym MFA. Logowanie hasłem, konto root,
  przekazywanie agenta i interaktywne konto współdzielone są wyłączone.
- Dozwolone są tylko potrzebne algorytmy kryptograficzne i aktualne wersje protokołu.
  `AllowTcpForwarding`, `PermitTunnel`, przekazywanie X11 i nieużywane podsystemy są
  wyłączone. Reguły są kontrolowane jako kod polityki.
- Konta i usługi mają najmniejszy możliwy zakres: osobna tożsamość operatora,
  osobna tożsamość usługi i krótkotrwałe certyfikaty. Każde użycie uprzywilejowanej
  operacji wymaga jawnego powodu i zostawia wpis audytowy.
- Zapora domyślnie odrzuca ruch przychodzący. Dozwolone są tylko endpointy
  aktualizacji, attestation, logowania i konieczne zależności biznesowe; reguły
  wychodzące są równie restrykcyjne.

## Centralne logowanie i audyt

Logi są wysyłane w sposób uwierzytelniony i szyfrowany do systemu poza hostem.
Obejmują co najmniej: start i wynik attestation, wersję obrazu, zmiany polityk,
logowania SSH, użycie `sudo`, decyzje operatora, żądania asystenta, wynik walidacji,
odmowy uprawnień, zatrzymania i prób odzyskiwania. Zawartość sekretów, tokenów,
pełnych danych osobowych i niepotrzebnych danych wejściowych jest redagowana przed
wysłaniem.

Dzienniki mają zsynchronizowany czas, ochronę przed modyfikacją (append-only lub
podpisy okresowe), retencję zgodną z polityką i kontrolę dostępu tylko do odczytu dla
audytorów. Brak centralnego logowania jest stanem bezpiecznym: usługa nie przyjmuje
nowych zadań i sygnalizuje alarm.

## Reagowanie na incydenty (IR)

1. **Wykrycie:** alert z attestation, integralności, SSH, anomalii uprawnień lub
   dziennika otwiera sprawę z identyfikatorem, czasem UTC i właścicielem.
2. **Ograniczenie:** natychmiast odciąć host od ruchu zadaniowego, unieważnić sesje,
   tokeny i certyfikaty oraz przełączyć system w tryb zatrzymania. Nie usuwać logów.
3. **Analiza:** zachować metadane obrazu, PCR, logi centralne i informacje o zmianach.
   Pobieranie danych ulotnych wykonuje wyłącznie uprawniony zespół, zgodnie z
   łańcuchem dowodowym i przepisami.
4. **Usunięcie i odtworzenie:** zbudować nowy, zweryfikowany obraz, odtworzyć tylko
   zatwierdzoną konfigurację, ponowić attestation i testy kontrolne. Nie przywracać
   niezweryfikowanego stanu z podejrzanego hosta.
5. **Wnioski:** udokumentować przyczynę, zakres, czas reakcji, decyzje człowieka i
   działania korygujące; zaktualizować reguły detekcji oraz procedury.

## Recovery i testy gotowości

Recovery wymaga znanego dobrego obrazu, kopii polityk, kluczy odzyskiwania przechowywanych
poza hostem, listy kontaktów IR i procedury rotacji wszystkich sekretów. Kopie są
szyfrowane, wersjonowane, testowane pod kątem odtworzenia i nie zawierają efemerycznych
danych roboczych.

Co najmniej okresowo należy wykonać ćwiczenie odtworzenia po: nieudanej attestation,
utracie hosta, kompromitacji tokenu, braku logowania i błędnej aktualizacji. Kryteria
akceptacji obejmują: brak uruchomienia niepodpisanego obrazu, pełną ścieżkę audytową,
skuteczne odcięcie kanału zadaniowego i potwierdzenie decyzji human-in-the-loop.

## Jawne wykluczenia

Projekt i wdrożenie **nie obejmują**: C2 (command and control), evasion, ukrytej
persistence, reverse shell, port knocking, eksfiltracji, komponentu „Shadow Agent”,
self-erasure ani mechanizmów obchodzenia kontroli, logowania lub zgody operatora.
Nie wolno dodawać takich funkcji pod inną nazwą ani jako „trybu awaryjnego”.
