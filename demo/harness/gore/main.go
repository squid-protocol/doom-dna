// DOOM-E13 headless driver for gore (our own code).
package main

import (
	"image"
	"os"

	"github.com/AndreRenaud/gore"
)

type headless struct{}

func (headless) DrawFrame(img *image.RGBA)                           {}
func (headless) SetTitle(title string)                               {}
func (headless) GetEvent(event *gore.DoomEvent) bool                 { return false }
func (headless) CacheSound(name string, data []byte)                 {}
func (headless) PlaySound(name string, channel, volume, sep int)     {}

func main() {
	defer gore.E13Close()
	gore.Run(headless{}, os.Args[1:])
}
