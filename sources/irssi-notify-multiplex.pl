#!/usr/bin/perl -w
use strict;

##
## Put me in ~/.irssi/scripts, and then execute the following in irssi:
##
##       /load perl
##       /script load notify
##

use strict;
use Irssi;
use vars qw($VERSION %IRSSI);
#use HTML::Entities;
use IO::Socket::UNIX qw( SOCK_DGRAM );

$VERSION = "0.5";
%IRSSI = (
    authors     => 'Steven Presser, based on irssi-libnotify by Luke Macken, Paul W. Frields',
    contact     => 'steve@pressers.name',
    name        => 'notify-multiplex.pl',
    description => 'Use notify-multiplex',
    license     => 'GNU General Public License',
    url         => '',
);

Irssi::settings_add_str('notify-multiplex', 'notify-multiplex-socket', "\0notify-multiplexer");

sub notify {
    my ($server, $summary, $message) = @_;
    #print 'Socket is' . Irssi::settings_get_str('notify-multiplex-socket');
    my $socket = IO::Socket::UNIX->new(
	Type => SOCK_DGRAM,
	Peer => "\0notify-multiplexer",
    ) or print 'Cant connect to socket';
    if ($socket) {
	my $fulltext = $summary . "\0" . $message . "\0im\0\0";
	print $socket $fulltext;
    }
    #print $fulltext
}
 
sub print_text_notify {
    my ($dest, $text, $stripped) = @_;
    my $server = $dest->{server};

    return if (!$server || !($dest->{level} & MSGLEVEL_HILIGHT));
    my $sender = $stripped;
    $sender =~ s/^\<.([^\>]+)\>.+/\1/ ;
    $stripped =~ s/^\<.[^\>]+\>.// ;
    my $summary = $dest->{target} . ": " . $sender;
    notify($server, $summary, $stripped);
}

sub message_private_notify {
    my ($server, $msg, $nick, $address) = @_;
    
    return if (!$server);
    notify($server, "PM from ".$nick, $msg);
}

sub dcc_request_notify {
    my ($dcc, $sendaddr) = @_;
    my $server = $dcc->{server};

    return if (!$dcc);
    notify($server, "DCC ".$dcc->{type}." request", $dcc->{nick});
}

Irssi::signal_add('print text', 'print_text_notify');
Irssi::signal_add('message private', 'message_private_notify');
Irssi::signal_add('dcc request', 'dcc_request_notify');