/**
 * @file    parser.h
 * @brief   Serial command parser — decodes text packets and
 *          dispatches motion / I/O commands.
 *
 * Serial protocol
 * ---------------
 * The Python host sends one or more semicolon-separated commands
 * as a single line, e.g.:
 *
 *   h;x4998s2000;y3724s2000;p1;r45;p0;END\n
 *
 * Command syntax
 * --------------
 *   x{pos}s{speed}   Move X to absolute step position
 *   y{pos}s{speed}   Move Y to absolute step position
 *   p1               Pick  (lower, suction ON, raise)
 *   p0               Place (lower, suction OFF, raise)
 *   r{angle}         Rotate piece [0–90°]
 *   h                Homing sequence
 *   d                Delay (CMD_DELAY_MS)
 *   END              Mark end of a packet → firmware replies "OK"
 *
 * Firmware replies
 * ----------------
 *   ACK{n}           Packet n received and executed (no END seen)
 *   OK               Packet contained END — all instructions done
 *   ERROR: ...       Malformed or unknown command
 *
 * Notes
 * -----
 * - The speed field in x/y commands is parsed and echoed back for
 *   logging but currently has no effect on motion speed (the axis
 *   speeds are set globally in config.h).  This is a known
 *   limitation and can be extended in moveX() / moveY().
 */

#pragma once

#include <Arduino.h>
#include "config.h"

/** True once an "END" command has been received in the current packet. */
extern bool instructions_done;
extern String instructions[MAX_INSTRUCTIONS];
extern int    instructionCount;
/**
 * @brief Split a raw semicolon-delimited string into the global
 *        instructions[] array.
 * @param raw  The full packet string as received from Serial.
 */
void parseInstructions(const String& raw);

/**
 * @brief Execute a single command string.
 * @param cmd  One command token, e.g. "x4998s2000" or "p1".
 */
void parseCommand(const String& cmd);
