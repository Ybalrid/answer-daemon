# Answer Daemon

This is a small python script I am hacking on to solve a very dumb problem:

An Olitec Self-Memory 33600 modem (cocorico!) seems to **not react properly** to analog ringing and hang-up signaling from my GrandStream HT802. The GrandStream is to blame, it does not simulate all the behavior of the old France Télécom PSTN properly.

For example, the ring signal generator output a 25 Hz AC voltage, not a 50 Hz.

I am attempting to use this modem to remote into a server from another analog modem (there's no good reasons why, it's just for fun).

Ultimately I want to try to run a BBS through this Olitec modem and this ATA.

## How it works

This daemon open and read from a UNIX socket located at /tmp/answer-daemon.sock. The modem is plugged to the actual Asterisk server in this setup (... yes, this means a machine on my network is looping on itself from SIP/RTP ethernet, to Analog telephone wire, to RS-232, to USB).

Currently the modem path is hard coded to /dev/ttyUSB0, because that works for me for now.

Whenever the daemon receive a command, it will interact with the serial port in such a way that causes the modem to do what we wanted it to do. For example:

- ASNWER will print ATA to the serial port, forcing the modem to pick up the line. The modem was oblivious to the fact that it was ringing, despite auto answer being configured.
- HANGUP will cause the script to drop the DTR line for 200 miliseconds. The modem and serial adapter all have hardware flow control that works, and this actually causes the modem to put the phone back on hook.
- AT is just here for debugging, it prints AT to the serial port, the modem answers OK, it proves that it's alive enough to receive commands.
