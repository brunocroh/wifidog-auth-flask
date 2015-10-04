function VoucherStore() {
    var self = this,
        base = '/api/vouchers';

    riot.observable(self);

    triggerUpdate = function() {
        $.getJSON(base, function(data) {
            self.trigger('vouchers.updated', data.objects);
        });
    };

    self.on('vouchers.create', function(minutes) {
        $.ajax({
            url: base,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                minutes
            }),
            success: triggerUpdate
        });
    });

    self.on('voucher.remove', function(id) {
        $.ajax({
            url: base + '/' + id,
            type: 'DELETE',
            success: triggerUpdate
        });
    });

    self.on('vouchers.remove', function() {
        $.ajax({
            url: base,
            type: 'DELETE',
            success: triggerUpdate
        });
    });
}

RiotControl.addStore(new VoucherStore());
