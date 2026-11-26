"""Build Managed Doom (C#) headless with the E13 per-tic digest. Usage: python build_manageddoom.py <managed-doom clone> <out_dir>
Copies ManagedDoom/src without the windowing layer (Silk/), adds our digest and console driver (Managed Doom's own null video/sound/music/input),
inserts one call after the level-time increment, exposes the RNG index, builds with the private .NET SDK."""
import os, re, shutil, subprocess, sys
from pathlib import Path
clone, out = Path(sys.argv[1]), Path(sys.argv[2]); H = Path(__file__).resolve().parent
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); DOTNET = W / "tools/dotnet/dotnet"
if out.exists(): shutil.rmtree(out)
shutil.copytree(clone / "ManagedDoom/src", out / "src", ignore=shutil.ignore_patterns("Silk"))
t = (out / "src/Doom/World/World.cs").read_text(); m = re.search(r"\n([ \t]*)levelTime\+\+;[^\n]*\n", t); assert m, "anchor not found"
(out / "src/Doom/World/World.cs").write_text(t[:m.end()] + f"{m.group(1)}E13Digest.Tick(this);\n" + t[m.end():])
r = (out / "src/Doom/Common/DoomRandom.cs").read_text(); a = "private int index;"; assert a in r
(out / "src/Doom/Common/DoomRandom.cs").write_text(r.replace(a, a + "\n        public int Index => index;", 1))
shutil.copy(H / "managed/E13Digest.cs", out / "src/E13Digest.cs")
(out / "E13.csproj").write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><AssemblyName>e13-managed-doom</AssemblyName><AllowUnsafeBlocks>True</AllowUnsafeBlocks><InvariantGlobalization>true</InvariantGlobalization><Nullable>disable</Nullable><ImplicitUsings>disable</ImplicitUsings><EnableDefaultCompileItems>false</EnableDefaultCompileItems></PropertyGroup><ItemGroup><Compile Include="src/**/*.cs" /></ItemGroup></Project>')
env = dict(os.environ, DOTNET_CLI_HOME=str(W / "tools/dotnet_home"), DOTNET_NOLOGO="1", DOTNET_SKIP_FIRST_TIME_EXPERIENCE="1", DOTNET_CLI_TELEMETRY_OPTOUT="1", PATH=f"{W}/tools/dotnet:/usr/bin:/bin")
r = subprocess.run([str(DOTNET), "build", "-c", "Release", "-o", str(out / "bin")], cwd=out, capture_output=True, text=True, env=env)
print(r.stdout[-1800:]); print(r.stderr[-1500:]); sys.exit(r.returncode)
